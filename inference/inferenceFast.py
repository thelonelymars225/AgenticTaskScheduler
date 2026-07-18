"""Fast, reliability-first local code-generation pipeline using Ollama."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ollama

from inference.pipeline_config import (
    ACCEPTANCE_TEST_TIMEOUT_SECONDS,
    CODER_MODEL,
    LOCAL_CODER_FALLBACK_MODEL,
    ENABLE_ACCEPTANCE_TESTS,
    ENABLE_LLM_REVIEW,
    ENABLE_PLANNING,
    MAX_REPAIRS,
    MODEL_KEEP_ALIVE,
    PLANNER_MODEL,
    PRIMARY_MODEL,
    QA_MODEL,
    STARTUP_GRACE_SECONDS,
    DEEPSEEK_ESCALATION_ENABLED,
    DEEPSEEK_ESCALATION_MODEL,
    DEEPSEEK_MAX_CALLS_PER_RUN,
)
from inference.deepseek_api import available as deepseek_available
from inference.deepseek_api import generate_code as deepseek_generate_code
from inference.deepseek_api import repair_code as deepseek_repair_code
from inference.trusted_benchmarks import get_trusted_suite
from timer import Timer

CLIENT = ollama.Client()
KEEP_ALIVE = MODEL_KEEP_ALIVE
STARTUP_GRACE = STARTUP_GRACE_SECONDS
CHAR_LIMITS = {"simple": 8000, "medium": 16000, "complex": 24000, "very_complex": 32000}
MEASUREMENT_STATUSES = {
    "VALID", "INVALID_HARNESS", "INVALID_EXPECTATION", "INFRA_FAIL",
    "NOT_EXECUTED", "NO_TESTS_COLLECTED",
}
CANDIDATE_STATUSES = {"PASS", "FAIL", "UNMEASURED"}
REPAIR_STATUSES = {"NOT_ATTEMPTED", "CHANGED", "UNCHANGED", "FAILED"}
_MODEL_CALL_EVENTS: list[dict[str, Any]] = []


@dataclass(frozen=True)
class TaskPlan:
    specification: list[str]
    implementation_plan: list[str]
    acceptance_tests: list[str]
    complexity: str = "medium"

    @property
    def char_limit(self) -> int:
        return CHAR_LIMITS.get(self.complexity, CHAR_LIMITS["medium"])

    def as_markdown(self) -> str:
        sections = [
            "## Specification\n" + "\n".join(f"- {x}" for x in self.specification),
            "## Implementation Plan\n" + "\n".join(f"- {x}" for x in self.implementation_plan),
            "## Acceptance Tests\n" + "\n".join(f"- {x}" for x in self.acceptance_tests),
        ]
        return "\n\n".join(sections) + f"\n\nCOMPLEXITY: {self.complexity}"


@dataclass
class ValidationResult:
    passed: bool
    failures: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


@dataclass
class ReviewResult:
    passed: bool
    issues: list[str] = field(default_factory=list)
    raw: str = ""

    def as_text(self) -> str:
        verdict = "PASS" if self.passed else "FAIL"
        details = "\n".join(f"- {x}" for x in self.issues)
        return f"VERDICT: {verdict}" + (f"\n{details}" if details else "")


@dataclass
class AcceptanceTestResult:
    passed: bool
    failures: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    executed: bool = False
    test_count: int = 0
    exit_code: int | None = None
    measurement_status: str = "NOT_EXECUTED"
    suite_version: str | None = None

    def __post_init__(self) -> None:
        if self.measurement_status not in MEASUREMENT_STATUSES:
            raise ValueError(f"Unsupported measurement status: {self.measurement_status}")


@dataclass
class AttemptRecord:
    number: int
    code: str
    validation: ValidationResult
    acceptance_tests: str
    acceptance_result: AcceptanceTestResult
    review: ReviewResult
    candidate_status: str = "UNMEASURED"
    repair_status: str = "NOT_ATTEMPTED"

    def __post_init__(self) -> None:
        if self.candidate_status not in CANDIDATE_STATUSES:
            raise ValueError(f"Unsupported candidate status: {self.candidate_status}")
        if self.repair_status not in REPAIR_STATUSES:
            raise ValueError(f"Unsupported repair status: {self.repair_status}")


@dataclass
class RepairEvent:
    repair_number: int
    source_attempt: int
    trigger: list[str]
    before_sha256: str
    after_sha256: str
    changed: bool
    model: str
    status: str
    duration_seconds: float

    def __post_init__(self) -> None:
        if self.status not in REPAIR_STATUSES - {"NOT_ATTEMPTED"}:
            raise ValueError(f"Unsupported repair event status: {self.status}")


@dataclass
class PipelineResult:
    task: TaskPlan
    code: str
    review: ReviewResult
    attempts: list[AttemptRecord]
    benchmark_id: str | None = None
    trusted_suite_version: str | None = None
    repair_events: list[RepairEvent] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    model_calls: list[dict[str, Any]] = field(default_factory=list)


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if not isinstance(x, (dict, list)) and str(x).strip()]
    if isinstance(value, (dict, tuple, set)):
        return []
    return [str(value).strip()] if value is not None and str(value).strip() else []


def _parse_plan_payload(text: str) -> TaskPlan:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = {
            "specification": [text.strip() or "Implement the user request."],
            "implementation_plan": ["Use a minimal reliable Python design."],
            "acceptance_tests": ["The program compiles and starts without an exception."],
            "complexity": "medium",
        }
    complexity = str(payload.get("complexity", "medium")).lower().replace("-", "_")
    if complexity not in CHAR_LIMITS:
        complexity = "medium"
    return TaskPlan(
        _as_list(payload.get("specification")) or ["Implement the user request."],
        _as_list(payload.get("implementation_plan") or payload.get("plan"))
        or ["Use a minimal reliable Python design."],
        _as_list(payload.get("acceptance_tests") or payload.get("tests"))
        or ["The program compiles and starts without an exception."],
        complexity,
    )


def _parse_review_payload(text: str) -> ReviewResult:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ReviewResult(False, [f"QA returned invalid JSON: {text[:500]}"], text)
    raw_issues = payload.get("issues")
    issues: list[str] = []
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if isinstance(item, str) and item.strip():
                issues.append(item.strip())
            elif isinstance(item, dict):
                # Some local models return richer objects despite the requested
                # string schema. Preserve their concrete evidence for repair.
                details = [
                    str(item[key]).strip()
                    for key in ("issue", "cause", "behavior", "root_cause")
                    if isinstance(item.get(key), str) and item[key].strip()
                ]
                if details:
                    issues.append(" — ".join(details))
    else:
        issues = _as_list(raw_issues)
    passed = str(payload.get("verdict", "FAIL")).upper() == "PASS" and not issues
    if not passed and not issues:
        issues = ["Quality review did not approve the implementation."]
    return ReviewResult(passed, issues, text)


def _strip_code_blocks(text: str) -> str:
    if not text:
        return ""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return max(blocks, key=len).strip() if blocks else text.strip()


def _chat(model: str, messages: list[dict[str, Any]], *, json_output: bool = False,
          num_predict: int = 2000, temperature: float = 0.1) -> str:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "keep_alive": KEEP_ALIVE,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    if json_output:
        kwargs["format"] = "json"
    started = time.perf_counter()
    response = CLIENT.chat(**kwargs)
    elapsed = time.perf_counter() - started

    def response_value(name: str) -> Any:
        if isinstance(response, dict):
            return response.get(name)
        return getattr(response, name, None)
    _MODEL_CALL_EVENTS.append({
        "call_number": len(_MODEL_CALL_EVENTS) + 1,
        "model": model,
        "duration_seconds": elapsed,
        "prompt_tokens": response_value("prompt_eval_count"),
        "output_tokens": response_value("eval_count"),
        "ollama_total_duration_ns": response_value("total_duration"),
        "ollama_load_duration_ns": response_value("load_duration"),
        "ollama_prompt_eval_duration_ns": response_value("prompt_eval_duration"),
        "ollama_eval_duration_ns": response_value("eval_duration"),
    })
    return response["message"]["content"]


def _sha256(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _candidate_status(validation: ValidationResult, acceptance: AcceptanceTestResult) -> str:
    """Derive candidate status only from valid executable measurement evidence."""
    if (
        acceptance.measurement_status != "VALID"
        or not acceptance.executed
        or acceptance.test_count < 1
        or acceptance.exit_code is None
    ):
        return "UNMEASURED"
    return "PASS" if validation.passed and acceptance.passed and acceptance.exit_code == 0 else "FAIL"


def _timing_totals(total_duration: float) -> dict[str, float]:
    stats = Timer.get_stats() if hasattr(Timer, "get_stats") else {}
    totals = {name: values["total"] for name, values in stats.items()}
    totals["pipeline.workflow"] = total_duration
    return totals


def analyze_task(prompt: str) -> TaskPlan:
    text = _chat(
        PLANNER_MODEL,
        [
            {"role": "system", "content": (
                "Return valid JSON only with specification, implementation_plan, acceptance_tests, and complexity. "
                "Complexity must be simple, medium, complex, or very_complex. Translate every explicit user request "
                "into a concrete, testable requirement; do not invent optional product features. For interactive or GUI "
                "programs, include startup, input, update-loop, and exit/smoke-test behavior. Acceptance tests must be "
                "concrete and observable, and must cover the important user flows and edge cases."
            )},
            {"role": "user", "content": prompt},
        ],
        json_output=True,
        num_predict=1500,
    )
    plan = _parse_plan_payload(text)
    # A malformed/empty planner response must not erase the original task:
    # downstream acceptance and review need the concrete benchmark requirements.
    if plan.specification == ["Implement the user request."] and prompt.strip():
        return TaskPlan([prompt.strip()], plan.implementation_plan, plan.acceptance_tests, plan.complexity)
    return plan


def _fast_task_plan(prompt: str) -> TaskPlan:
    """Build the minimum useful plan without spending a model request."""
    request = prompt.strip() or "Implement the user request."
    return TaskPlan(
        specification=[request],
        implementation_plan=["Implement the smallest complete Python solution."],
        acceptance_tests=["The generated source compiles and exits successfully with AGENT_SMOKE_TEST=1."],
        complexity="medium",
    )


def _token_budget(task: TaskPlan) -> int:
    return max(1500, min(10000, task.char_limit // 3))


def write_code(prompt: str, task: TaskPlan, model: str = CODER_MODEL,
               failures: list[str] | None = None) -> str:
    failure_text = ""
    if failures:
        failure_text = "\nPrevious failures:\n" + "\n".join(f"- {x[:800]}" for x in failures[-8:])
    messages = [
            {"role": "system", "content": (
                "Return only complete executable Python source. Build the smallest reliable solution. "
                "The program must compile and start. When AGENT_SMOKE_TEST=1, perform only a safe startup/liveness "
                "probe and exit 0 rather than blocking. Do not put task-behavior assertions or hand-calculated expected "
                "outputs in the smoke path; an independent acceptance test verifies behavior. Use os.getenv('AGENT_SMOKE_TEST') exactly; do not "
                "use a Python global for this protocol. Keep core behavior separable from UI/framework code so an "
                "independent standard-library test script can exercise it without a display, network, or user input. "
                f"Keep source below {task.char_limit} characters."
            )},
            {"role": "user", "content": f"Request:\n{prompt}\n\n{task.as_markdown()}{failure_text}"},
        ]
    if model.startswith("deepseek-api:") and deepseek_available():
        generated = deepseek_generate_code(
            prompt,
            task.as_markdown() + failure_text,
            model=model.split(":", 1)[1],
            record_call=_record_external_call,
        )
        if generated:
            return generated
        model = LOCAL_CODER_FALLBACK_MODEL
    text = _chat(model, messages, num_predict=_token_budget(task), temperature=0.1)
    return _strip_code_blocks(text)


def _record_external_call(metadata: dict[str, Any]) -> None:
    metadata["call_number"] = len(_MODEL_CALL_EVENTS) + 1
    _MODEL_CALL_EVENTS.append(metadata)


def repair_code(code: str, task: TaskPlan, failures: list[str]) -> str:
    failure_text = "\n".join(f"- {x[:1000]}" for x in failures[-8:])
    messages = [
            {"role": "system", "content": (
                "Return only the complete corrected Python source. Make the smallest changes needed to fix every "
                "reported failure as one coherent fix; do not address only the first bullet or add cosmetic no-op "
                "changes. Re-check control flow, state updates, and required user-visible behavior after the change. "
                "Keep AGENT_SMOKE_TEST=1 as a liveness-only non-blocking path; do not add behavioral assertions there."
            )},
            {"role": "user", "content": (
                f"{task.as_markdown()}\n\nFailures:\n{failure_text}\n\nCurrent code:\n```python\n{code}\n```"
            )},
        ]
    if CODER_MODEL.startswith("deepseek-api:") and deepseek_available():
        repaired = deepseek_repair_code(
            code,
            task.as_markdown(),
            failures,
            model=CODER_MODEL.split(":", 1)[1],
            record_call=_record_external_call,
        )
        if repaired:
            return repaired
    text = _chat(LOCAL_CODER_FALLBACK_MODEL, messages, num_predict=_token_budget(task), temperature=0.05)
    return _strip_code_blocks(text)


def validate_syntax(code: str) -> str:
    try:
        compile(code, "<generated>", "exec")
        return ""
    except SyntaxError as exc:
        return f"SyntaxError at line {exc.lineno}: {exc.msg}"


def _terminate(proc: subprocess.Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    try:
        if hasattr(os, "killpg"):
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=2)
        except Exception:
            pass


def runtime_check(code: str, startup_grace: float = STARTUP_GRACE) -> ValidationResult:
    with tempfile.TemporaryDirectory(prefix="agentic-task-") as directory:
        root = Path(directory)
        source = root / "generated.py"
        stdout_path = root / "stdout.txt"
        stderr_path = root / "stderr.txt"
        source.write_text(code, encoding="utf-8")
        env = os.environ.copy()
        env["AGENT_SMOKE_TEST"] = "1"
        with stdout_path.open("w") as stdout_file, stderr_path.open("w") as stderr_file:
            try:
                proc = subprocess.Popen(
                    [sys.executable, str(source)], cwd=root, env=env,
                    stdout=stdout_file, stderr=stderr_file, start_new_session=True,
                )
            except OSError as exc:
                return ValidationResult(False, [f"Could not start generated program: {exc}"])
            deadline = time.monotonic() + startup_grace
            while time.monotonic() < deadline and proc.poll() is None:
                time.sleep(0.1)
            exit_code = proc.poll()
            _terminate(proc)
        stdout = stdout_path.read_text(errors="replace")[-4000:]
        stderr = stderr_path.read_text(errors="replace")[-4000:]
        if exit_code is not None and exit_code != 0:
            detail = stderr.strip() or stdout.strip() or f"Process exited with code {exit_code}."
            return ValidationResult(False, [f"Runtime failure: {detail}"], stdout, stderr)
        if exit_code is None:
            return ValidationResult(
                False,
                [
                    "Smoke test did not exit within "
                    f"{startup_grace:g} seconds while AGENT_SMOKE_TEST=1."
                ],
                stdout,
                stderr,
            )
        return ValidationResult(True, stdout=stdout, stderr=stderr)


def validate_code(code: str, task: TaskPlan) -> ValidationResult:
    failures: list[str] = []
    if not code.strip():
        return ValidationResult(False, ["Generated code is empty."])
    if len(code) > task.char_limit:
        failures.append(f"Source is {len(code)} characters; limit is {task.char_limit}.")
    syntax_error = validate_syntax(code)
    if syntax_error:
        failures.append(syntax_error)
        return ValidationResult(False, failures)
    runtime = runtime_check(code)
    failures.extend(runtime.failures)
    return ValidationResult(not failures, failures, runtime.stdout, runtime.stderr)


def write_acceptance_tests(code: str, task: TaskPlan) -> str:
    """Ask an independent QA role for a standard-library executable test harness."""
    messages = [
            {"role": "system", "content": (
                "Return only a complete Python test script using the standard library. The generated candidate path "
                "is in os.environ['CANDIDATE_PATH']. The script MUST import and execute that candidate via "
                "importlib.util.spec_from_file_location; a script that reimplements the solution or does not reference "
                "CANDIDATE_PATH is invalid. Test the explicit acceptance requirements using observable "
                "behavior, not style. Do not invent APIs: inspect the candidate and use public functions/classes it "
                "actually provides. Never instantiate tkinter.Tk(), Canvas, or any GUI/window: for GUI candidates, "
                "load the candidate before defining test functions; never copy or reimplement candidate behavior in the harness. "
                "test pure logic with fakes or mocks only. If no headless interface can be exercised, raise one clear "
                "AssertionError without opening a window. If testing a CLI, create its temporary input and invoke it "
                "with explicit arguments (or call its public functions); never rely on the test runner's empty argv. "
                "When writing JSON test data, prefer a temporary pathlib.Path: write with Path.write_text(json.dumps(...), "
                "encoding='utf-8') and read it through the candidate using explicit paths. If a temporary handle is unavoidable, "
                "use mode='w+', encoding='utf-8', then flush() and seek(0) before every read. Do not pass text to a binary temporary file. "
                "For subprocess stdin, pass an open file handle or input text, never a filename string. If using sys.argv or sys.executable, "
                "include the corresponding import. "
                "Exercise at least one valid case and one invalid/edge case. Avoid network calls, sleeps, and third-party packages. Exit non-zero "
                "or raise AssertionError when a required behavior fails. If an acceptance requirement cannot be tested "
                "from the candidate, fail with a clear assertion explaining the missing testable interface."
            )},
            {"role": "user", "content": (
                f"{task.as_markdown()}\n\nCandidate:\n```python\n{code}\n```"
            )},
        ]
    text = _chat(
        QA_MODEL,
        messages,
        num_predict=1800,
        temperature=0.0,
    )
    tests = _strip_code_blocks(text)
    if _acceptance_harness_violations(tests):
        correction = (
            "Your previous test script violated the harness contract. Regenerate it now. "
            "It must import CANDIDATE_PATH with spec_from_file_location, never instantiate tkinter.Tk or tkinter.Canvas, "
            "must load the candidate before defining test functions and must not copy its implementation, "
            "must prefer pathlib.Path for JSON fixtures or use text-mode NamedTemporaryFile(mode='w+', encoding='utf-8'), "
            "flush and seek(0) before every same-handle read, pass a file handle or input text to subprocess stdin, "
            "must import every module it references, and must exercise a valid and invalid case without relying on empty argv. "
            "Return only the corrected script."
        )
        retry_messages = [*messages, {"role": "user", "content": correction}]
        tests = _strip_code_blocks(_chat(QA_MODEL, retry_messages, num_predict=1800, temperature=0.0))
    # A missing standard-library import is a harness construction defect, not
    # candidate evidence. Normalize this safe, unambiguous case after retry.
    for module in ("sys", "argparse", "os", "json", "io"):
        if re.search(rf"\b{module}\.", tests) and not re.search(rf"^\s*import\s+{module}\b", tests, re.MULTILINE):
            tests = f"import {module}\n" + tests
    tests = re.sub(r"(NamedTemporaryFile\([^\n]*mode\s*=\s*['\"])w(['\"])", r"\1w+\2", tests)
    if "NamedTemporaryFile" in tests and ("json.dump" in tests or "json.load" in tests):
        tests = re.sub(
            r"NamedTemporaryFile\(\)",
            "NamedTemporaryFile(mode='w+', encoding='utf-8')",
            tests,
        )
    tests = re.sub(
        r"(?m)^(\s*os\.environ\[[^\n]+\]\s*=\s*)Path\((.*)\)\s*$",
        r"\1str(Path(\2))",
        tests,
    )
    return _normalize_acceptance_harness(tests)


def _normalize_acceptance_harness(tests: str) -> str:
    """Apply safe mechanical fixes before validating or executing a harness."""
    lines = tests.splitlines()
    temp_vars = re.findall(r"NamedTemporaryFile\([^\n]*\)\s+as\s+(\w+)", tests)
    normalized: list[str] = []
    for line in lines:
        matched_var = next(
            (variable for variable in temp_vars if re.search(rf"json\.load\s*\(\s*{variable}\s*\)", line)),
            None,
        )
        if matched_var:
            indent = line[: len(line) - len(line.lstrip())]
            recent = normalized[-3:]
            if not any(re.search(rf"\b{matched_var}\.seek\s*\(\s*0\s*\)", item) for item in recent):
                normalized.extend([f"{indent}{matched_var}.flush()", f"{indent}{matched_var}.seek(0)"])
        normalized.append(line)
    return "\n".join(normalized) + ("\n" if tests.endswith("\n") else "")


def _acceptance_test_inventory(tests: str) -> tuple[list[str], list[str], int]:
    """Return runnable plain functions, unittest classes, and check count."""
    try:
        tree = ast.parse(tests)
    except SyntaxError:
        return [], [], 0
    test_names = [
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    test_classes: list[str] = []
    class_method_count = 0
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        count = sum(
            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_")
            for item in node.body
        )
        if count:
            test_classes.append(node.name)
            class_method_count += count
    if test_names or test_classes:
        return test_names, test_classes, len(test_names) + class_method_count
    top_level_checks = sum(
        isinstance(node, ast.Assert)
        or (
            isinstance(node, ast.Raise)
            and isinstance(node.exc, ast.Call)
            and isinstance(node.exc.func, ast.Name)
            and node.exc.func.id == "AssertionError"
        )
        for node in tree.body
    )
    return [], [], top_level_checks


def _acceptance_harness_violations(tests: str) -> list[str]:
    """Return deterministic contract violations before running a test harness."""
    violations: list[str] = []
    try:
        tree = ast.parse(tests)
    except SyntaxError as exc:
        return [f"test script does not parse at line {exc.lineno}: {exc.msg}"]
    if "CANDIDATE_PATH" not in tests or "spec_from_file_location" not in tests:
        violations.append("it must import the candidate through CANDIDATE_PATH")
    candidate_load = tests.find("spec_from_file_location")
    first_function = re.search(r"^\s*def\s+", tests, re.MULTILINE)
    if candidate_load >= 0 and first_function and first_function.start() < candidate_load:
        violations.append("the candidate must be loaded before test functions; do not duplicate its implementation")
    if re.search(r"(?:import\s+tkinter|from\s+tkinter|(?:tkinter|tk)\.(?:Tk|Canvas)\s*\()", tests):
        violations.append("it must not import or instantiate GUI objects in headless acceptance")
    if "NamedTemporaryFile" in tests and not re.search(r"NamedTemporaryFile\([^)]*mode\s*=\s*['\"]w\+?['\"]", tests):
        violations.append("text JSON must not be written to a binary NamedTemporaryFile")
    if re.search(r"NamedTemporaryFile\([^)]*mode\s*=\s*['\"]w['\"]", tests) and re.search(r"json\.load\s*\(\s*\w+\s*\)", tests):
        violations.append("a write-only temporary file must not be read; use mode='w+' or reopen it")
    lines = tests.splitlines()
    temp_vars = re.findall(r"NamedTemporaryFile\([^\n]*\)\s+as\s+(\w+)", tests)
    for variable in temp_vars:
        for index, line in enumerate(lines):
            if not re.search(rf"json\.load\s*\(\s*{variable}\s*\)", line):
                continue
            preceding = lines[max(0, index - 3):index]
            if not any(re.search(rf"\b{variable}\.seek\s*\(\s*0\s*\)", item) for item in preceding):
                violations.append(f"temporary file {variable} must be rewound before json.load")
                break
    if re.search(r"subprocess\.run\([^\n]*stdin\s*=\s*\w+\.name", tests):
        violations.append("subprocess stdin must be a file handle or input text, not a filename string")
    if re.search(r"\bsys\.", tests) and not re.search(r"^\s*import\s+sys\b", tests, re.MULTILINE):
        violations.append("it references sys without importing sys")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            if node.args.args or node.args.posonlyargs or node.args.kwonlyargs:
                violations.append(f"test function {node.name} requires unsupported fixture arguments")
    if re.search(r"\bPath\(\s*['\"][^/'\"][^'\"]*['\"]\s*\)", tests):
        violations.append("test fixtures must not depend on current-working-directory relative paths")
    return violations


def run_acceptance_tests(code: str, tests: str,
                         timeout: float = ACCEPTANCE_TEST_TIMEOUT_SECONDS) -> AcceptanceTestResult:
    """Run generated acceptance tests in an isolated temporary directory."""
    if not tests.strip():
        return AcceptanceTestResult(
            False,
            ["Independent acceptance test generator returned no test script."],
            measurement_status="INVALID_HARNESS",
        )
    tests = _normalize_acceptance_harness(tests)
    violations = _acceptance_harness_violations(tests)
    if violations:
        return AcceptanceTestResult(
            False,
            ["Invalid acceptance harness: " + "; ".join(violations) + "."],
            measurement_status="INVALID_HARNESS",
        )
    test_names, test_classes, test_count = _acceptance_test_inventory(tests)
    if test_count == 0:
        return AcceptanceTestResult(
            False,
            ["No executable acceptance tests were collected."],
            measurement_status="NO_TESTS_COLLECTED",
        )
    with tempfile.TemporaryDirectory(prefix="agentic-acceptance-") as directory:
        root = Path(directory)
        candidate = root / "candidate.py"
        test_file = root / "acceptance_tests.py"
        runner = root / "acceptance_runner.py"
        candidate.write_text(code, encoding="utf-8")
        test_file.write_text(tests, encoding="utf-8")
        runner.write_text(
            "import pathlib\nimport unittest\n"
            f"script = pathlib.Path({str(test_file)!r})\n"
            "namespace = {'__name__': 'acceptance_harness', '__file__': str(script)}\n"
            "exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), namespace)\n"
            f"for name in {test_names!r}:\n"
            "    namespace[name]()\n"
            f"suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(namespace[name]) for name in {test_classes!r})\n"
            "if suite.countTestCases() and not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():\n"
            "    raise SystemExit(1)\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["CANDIDATE_PATH"] = str(candidate)
        try:
            result = subprocess.run(
                [sys.executable, str(runner)], cwd=root, env=env,
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return AcceptanceTestResult(
                False, [f"Acceptance tests timed out after {timeout:g} seconds."],
                exc.stdout or "", exc.stderr or "", True, test_count, None, "INFRA_FAIL",
            )
        except OSError as exc:
            return AcceptanceTestResult(
                False, [f"Could not run acceptance tests: {exc}"],
                executed=False, test_count=test_count, measurement_status="INFRA_FAIL",
            )
    stdout = result.stdout[-4000:]
    stderr = result.stderr[-4000:]
    if result.returncode != 0:
        detail = stderr.strip() or stdout.strip() or f"Test process exited with code {result.returncode}."
        return AcceptanceTestResult(
            False, [f"Acceptance failure: {detail}"], stdout, stderr,
            True, test_count, result.returncode, "VALID",
        )
    return AcceptanceTestResult(
        True, stdout=stdout, stderr=stderr, executed=True,
        test_count=test_count, exit_code=result.returncode, measurement_status="VALID",
    )


def _review_response_is_invalid(text: str, review: ReviewResult) -> bool:
    return not text.strip() or any(issue.startswith("QA returned invalid JSON:") for issue in review.issues)


def quality_review(code: str, task: TaskPlan, evidence: list[str] | None = None) -> ReviewResult:
    evidence_text = ""
    if evidence:
        evidence_text = "\n\nExecution evidence:\n" + "\n".join(f"- {item}" for item in evidence)
    messages = [
        {"role": "system", "content": (
            "Return valid JSON only: {\"verdict\":\"PASS\"|\"FAIL\",\"issues\":[\"specific issue\"]}. "
            "Act as an adversarial code reviewer: trace actual control flow and method calls instead of assuming that "
            "plausible-looking code works. PASS only if every required behavior and acceptance test is implemented. "
            "On FAIL, list every independently actionable root cause you can verify (up to six), prioritizing causes "
            "that block a required behavior; do not stop at the first symptom or suggest cosmetic changes. "
            "For GUI or interactive code, verify event bindings, the scheduled update loop, rendering, collision/state "
            "changes, restart behavior, and the AGENT_SMOKE_TEST=1 exit path when applicable. Report only actionable "
            "issues with the relevant class, function, or behavior. Ignore optional improvements."
        )},
        {"role": "user", "content": f"{task.as_markdown()}\n\nCode:\n```python\n{code}\n```{evidence_text}"},
    ]
    for _ in range(2):
        text = _chat(QA_MODEL, messages, json_output=True, num_predict=1200, temperature=0.0)
        review = _parse_review_payload(text)
        if not _review_response_is_invalid(text, review):
            return review
    return ReviewResult(False, ["QA unavailable: reviewer returned no valid structured response after one retry."])


def project_management_with_attempts(
    prompt: str,
    max_retries: int = MAX_REPAIRS,
    benchmark_id: str | None = None,
) -> PipelineResult:
    """Generate and measure candidates, using frozen suites for known benchmark IDs."""
    max_retries = max(0, min(max_retries, MAX_REPAIRS))
    workflow_started = time.perf_counter()
    Timer.reset_all()
    _MODEL_CALL_EVENTS.clear()
    trusted_suite = get_trusted_suite(benchmark_id)
    with Timer("pipeline.analyze"):
        task = analyze_task(prompt) if ENABLE_PLANNING else _fast_task_plan(prompt)
    with Timer("pipeline.generate"):
        code = write_code(prompt, task)

    attempts: list[AttemptRecord] = []
    repair_events: list[RepairEvent] = []
    review = ReviewResult(False, ["Pipeline did not complete."])
    repair_status_for_attempt = "NOT_ATTEMPTED"
    deepseek_calls = 0
    for attempt in range(max_retries + 1):
        with Timer(f"pipeline.validate.{attempt + 1}"):
            validation = validate_code(code, task)
        acceptance_tests = ""
        acceptance = AcceptanceTestResult(
            False,
            ["Acceptance was not executed."],
            executed=False,
            measurement_status="NOT_EXECUTED",
            suite_version=trusted_suite.version if trusted_suite else None,
        )
        if validation.passed and ENABLE_ACCEPTANCE_TESTS:
            if trusted_suite:
                acceptance_tests = trusted_suite.source
            else:
                with Timer(f"pipeline.acceptance.generate.{attempt + 1}"):
                    acceptance_tests = write_acceptance_tests(code, task)
            with Timer(f"pipeline.acceptance.run.{attempt + 1}"):
                acceptance = run_acceptance_tests(code, acceptance_tests)
            acceptance.suite_version = trusted_suite.version if trusted_suite else None

        candidate_status = _candidate_status(validation, acceptance)
        evidence = [*validation.failures, *acceptance.failures]
        if trusted_suite:
            review = ReviewResult(
                candidate_status == "PASS",
                [] if candidate_status == "PASS" else evidence,
                f"trusted-suite:{trusted_suite.benchmark_id}:{trusted_suite.version}",
            )
        elif ENABLE_LLM_REVIEW:
            with Timer(f"pipeline.review.{attempt + 1}"):
                review = quality_review(code, task, evidence)
        else:
            review = ReviewResult(True)

        attempt_record = AttemptRecord(
            attempt + 1,
            code,
            validation,
            acceptance_tests,
            acceptance,
            review,
            candidate_status,
            repair_status_for_attempt,
        )
        attempts.append(attempt_record)
        completed = candidate_status == "PASS" if trusted_suite else (
            validation.passed and acceptance.passed and review.passed
        )
        if completed:
            break

        invalid_measurement = acceptance.measurement_status in {
            "INVALID_HARNESS", "INVALID_EXPECTATION", "INFRA_FAIL", "NO_TESTS_COLLECTED",
        }
        if invalid_measurement:
            break
        if any(issue.startswith("QA unavailable:") for issue in review.issues):
            break
        if attempt < max_retries:
            trigger = [*evidence]
            if not trusted_suite:
                trigger.extend(review.issues)
            trigger = [item for item in trigger if item][:8]
            before_sha256 = _sha256(code)
            repair_started = time.perf_counter()
            repair_model = CODER_MODEL
            try:
                with Timer(f"pipeline.repair.{len(repair_events) + 1}"):
                    repaired = repair_code(code, task, trigger)
                    # Escalate only after a valid executable measurement has
                    # failed.  This preserves cheap local generation while
                    # giving difficult candidates one stronger repair pass.
                    if (
                        DEEPSEEK_ESCALATION_ENABLED
                        and trusted_suite is not None
                        and acceptance.measurement_status == "VALID"
                        and deepseek_available()
                        and deepseek_calls < DEEPSEEK_MAX_CALLS_PER_RUN
                    ):
                        def record_deepseek_call(metadata: dict[str, Any]) -> None:
                            metadata["call_number"] = len(_MODEL_CALL_EVENTS) + 1
                            _MODEL_CALL_EVENTS.append(metadata)

                        escalated = deepseek_repair_code(
                            code,
                            task.as_markdown(),
                            trigger,
                            model=DEEPSEEK_ESCALATION_MODEL,
                            record_call=record_deepseek_call,
                        )
                        if escalated:
                            repaired = escalated
                            deepseek_calls += 1
                            repair_model = f"{CODER_MODEL} -> deepseek-api:{DEEPSEEK_ESCALATION_MODEL}"
            except Exception as exc:
                duration = time.perf_counter() - repair_started
                repair_events.append(RepairEvent(
                    len(repair_events) + 1,
                    attempt + 1,
                    trigger,
                    before_sha256,
                    before_sha256,
                    False,
                    repair_model,
                    "FAILED",
                    duration,
                ))
                review = ReviewResult(False, [*review.issues, f"Repair invocation failed: {exc}"], review.raw)
                break
            duration = time.perf_counter() - repair_started
            changed = repaired.strip() != code.strip()
            status = "CHANGED" if changed else "UNCHANGED"
            repair_events.append(RepairEvent(
                len(repair_events) + 1,
                attempt + 1,
                trigger,
                before_sha256,
                _sha256(repaired),
                changed,
                repair_model,
                status,
                duration,
            ))
            if not changed:
                review = ReviewResult(
                    False,
                    [*review.issues, "Repair returned an unchanged candidate; stopping the loop."],
                    review.raw,
                )
                break
            code = repaired
            repair_status_for_attempt = "CHANGED"

    Timer.print_stats()
    workflow_duration = time.perf_counter() - workflow_started
    return PipelineResult(
        task=task,
        code=code,
        review=review,
        attempts=attempts,
        benchmark_id=benchmark_id,
        trusted_suite_version=trusted_suite.version if trusted_suite else None,
        repair_events=repair_events,
        timings=_timing_totals(workflow_duration),
        model_calls=[dict(event) for event in _MODEL_CALL_EVENTS],
    )


def project_management(prompt: str, max_retries: int = MAX_REPAIRS) -> tuple[str, str, str]:
    """Compatibility wrapper returning the latest candidate and its QA verdict."""
    result = project_management_with_attempts(prompt, max_retries)
    return result.task.as_markdown(), result.code, result.review.as_text()
