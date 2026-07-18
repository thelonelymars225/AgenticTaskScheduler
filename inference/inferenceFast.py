"""Fast, reliability-first local code-generation pipeline using Ollama."""
from __future__ import annotations

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
    ENABLE_ACCEPTANCE_TESTS,
    ENABLE_LLM_REVIEW,
    ENABLE_PLANNING,
    ESCALATION_MODEL,
    MAX_REPAIRS,
    MODEL_KEEP_ALIVE,
    PLANNER_MODEL,
    PRIMARY_MODEL,
    QA_MODEL,
    STARTUP_GRACE_SECONDS,
)
from timer import Timer

CLIENT = ollama.Client()
KEEP_ALIVE = MODEL_KEEP_ALIVE
STARTUP_GRACE = STARTUP_GRACE_SECONDS
CHAR_LIMITS = {"simple": 8000, "medium": 16000, "complex": 24000, "very_complex": 32000}


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


@dataclass
class AttemptRecord:
    number: int
    code: str
    validation: ValidationResult
    acceptance_tests: str
    acceptance_result: AcceptanceTestResult
    review: ReviewResult


@dataclass
class PipelineResult:
    task: TaskPlan
    code: str
    review: ReviewResult
    attempts: list[AttemptRecord]


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
    response = CLIENT.chat(**kwargs)
    return response["message"]["content"]


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
    text = _chat(
        model,
        [
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
        ],
        num_predict=_token_budget(task),
        temperature=0.1,
    )
    return _strip_code_blocks(text)


def repair_code(code: str, task: TaskPlan, failures: list[str]) -> str:
    failure_text = "\n".join(f"- {x[:1000]}" for x in failures[-8:])
    text = _chat(
        CODER_MODEL,
        [
            {"role": "system", "content": (
                "Return only the complete corrected Python source. Make the smallest changes needed to fix every "
                "reported failure as one coherent fix; do not address only the first bullet or add cosmetic no-op "
                "changes. Re-check control flow, state updates, and required user-visible behavior after the change. "
                "Keep AGENT_SMOKE_TEST=1 as a liveness-only non-blocking path; do not add behavioral assertions there."
            )},
            {"role": "user", "content": (
                f"{task.as_markdown()}\n\nFailures:\n{failure_text}\n\nCurrent code:\n```python\n{code}\n```"
            )},
        ],
        num_predict=_token_budget(task),
        temperature=0.05,
    )
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
                "test pure logic with fakes or mocks only. If no headless interface can be exercised, raise one clear "
                "AssertionError without opening a window. If testing a CLI, create its temporary input and invoke it "
                "with explicit arguments (or call its public functions); never rely on the test runner's empty argv. "
                "When writing JSON or text to temporary files, use pathlib.Path or tempfile.NamedTemporaryFile(mode='w', "
                "encoding='utf-8'); do not pass text to a binary temporary file. If using sys.argv or sys.executable, "
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
            "must use text-mode temporary files (NamedTemporaryFile(mode='w', encoding='utf-8') or pathlib.Path), "
            "must import every module it references, and must exercise a valid and invalid case without relying on empty argv. "
            "Return only the corrected script."
        )
        retry_messages = [*messages, {"role": "user", "content": correction}]
        tests = _strip_code_blocks(_chat(QA_MODEL, retry_messages, num_predict=1800, temperature=0.0))
    return tests


def _acceptance_harness_violations(tests: str) -> list[str]:
    """Return deterministic contract violations before running a test harness."""
    violations: list[str] = []
    if "CANDIDATE_PATH" not in tests or "spec_from_file_location" not in tests:
        violations.append("it must import the candidate through CANDIDATE_PATH")
    if re.search(r"(?:import\s+tkinter|from\s+tkinter|(?:tkinter|tk)\.(?:Tk|Canvas)\s*\()", tests):
        violations.append("it must not import or instantiate GUI objects in headless acceptance")
    if "NamedTemporaryFile" in tests and not re.search(r"NamedTemporaryFile\([^)]*mode\s*=\s*['\"]w['\"]", tests):
        violations.append("text JSON must not be written to a binary NamedTemporaryFile")
    if re.search(r"\bsys\.", tests) and not re.search(r"^\s*import\s+sys\b", tests, re.MULTILINE):
        violations.append("it references sys without importing sys")
    return violations


def run_acceptance_tests(code: str, tests: str,
                         timeout: float = ACCEPTANCE_TEST_TIMEOUT_SECONDS) -> AcceptanceTestResult:
    """Run generated acceptance tests in an isolated temporary directory."""
    if not tests.strip():
        return AcceptanceTestResult(False, ["Independent acceptance test generator returned no test script."], executed=True)
    violations = _acceptance_harness_violations(tests)
    if violations:
        return AcceptanceTestResult(
            False,
            ["Invalid acceptance harness: " + "; ".join(violations) + "."],
            executed=True,
        )
    with tempfile.TemporaryDirectory(prefix="agentic-acceptance-") as directory:
        root = Path(directory)
        candidate = root / "candidate.py"
        test_file = root / "acceptance_tests.py"
        candidate.write_text(code, encoding="utf-8")
        test_file.write_text(tests, encoding="utf-8")
        env = os.environ.copy()
        env["CANDIDATE_PATH"] = str(candidate)
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)], cwd=root, env=env,
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return AcceptanceTestResult(
                False, [f"Acceptance tests timed out after {timeout:g} seconds."],
                exc.stdout or "", exc.stderr or "", True,
            )
        except OSError as exc:
            return AcceptanceTestResult(False, [f"Could not run acceptance tests: {exc}"], executed=True)
    stdout = result.stdout[-4000:]
    stderr = result.stderr[-4000:]
    if result.returncode != 0:
        detail = stderr.strip() or stdout.strip() or f"Test process exited with code {result.returncode}."
        return AcceptanceTestResult(False, [f"Acceptance failure: {detail}"], stdout, stderr, True)
    return AcceptanceTestResult(True, stdout=stdout, stderr=stderr, executed=True)


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


def project_management_with_attempts(prompt: str, max_retries: int = MAX_REPAIRS) -> PipelineResult:
    max_retries = max(0, min(max_retries, MAX_REPAIRS))
    Timer.reset_all()
    with Timer("pipeline.analyze"):
        task = analyze_task(prompt) if ENABLE_PLANNING else _fast_task_plan(prompt)
    with Timer("pipeline.generate"):
        code = write_code(prompt, task)

    failures: list[str] = []
    attempts: list[AttemptRecord] = []
    review = ReviewResult(False, ["Pipeline did not complete."])
    for attempt in range(max_retries + 1):
        with Timer(f"pipeline.validate.{attempt + 1}"):
            validation = validate_code(code, task)
        acceptance_tests = ""
        # The default profile deliberately skips generated deep acceptance tests
        # for speed. Keep that distinct from a passing executed test in artifacts.
        acceptance = AcceptanceTestResult(True, executed=False)
        if validation.passed and ENABLE_ACCEPTANCE_TESTS:
            with Timer(f"pipeline.acceptance.generate.{attempt + 1}"):
                acceptance_tests = write_acceptance_tests(code, task)
            with Timer(f"pipeline.acceptance.run.{attempt + 1}"):
                acceptance = run_acceptance_tests(code, acceptance_tests)

        evidence = [*validation.failures, *acceptance.failures]
        if ENABLE_LLM_REVIEW:
            with Timer(f"pipeline.review.{attempt + 1}"):
                review = quality_review(code, task, evidence)
        else:
            review = ReviewResult(True)

        attempt_record = AttemptRecord(attempt + 1, code, validation, acceptance_tests, acceptance, review)
        attempts.append(attempt_record)
        if validation.passed and acceptance.passed and review.passed:
            Timer.print_stats()
            return PipelineResult(task, code, review, attempts)

        failures.extend(evidence)
        failures.extend(review.issues)
        if any(issue.startswith("QA unavailable:") for issue in review.issues):
            break
        if attempt < max_retries:
            with Timer(f"pipeline.repair.{attempt + 1}"):
                repaired = repair_code(code, task, failures)
            if repaired.strip() == code.strip():
                review = ReviewResult(False, [*review.issues, "Repair returned an unchanged candidate; stopping the loop."], review.raw)
                break
            code = repaired

    if ESCALATION_MODEL and ESCALATION_MODEL != CODER_MODEL:
        with Timer("pipeline.escalate"):
            code = write_code(prompt, task, ESCALATION_MODEL, failures)
        validation = validate_code(code, task)
        acceptance_tests = write_acceptance_tests(code, task) if validation.passed and ENABLE_ACCEPTANCE_TESTS else ""
        acceptance = run_acceptance_tests(code, acceptance_tests) if acceptance_tests else AcceptanceTestResult(validation.passed, executed=False)
        review = quality_review(code, task, [*validation.failures, *acceptance.failures]) if ENABLE_LLM_REVIEW else ReviewResult(True)
        attempts.append(AttemptRecord(len(attempts) + 1, code, validation, acceptance_tests, acceptance, review))

    Timer.print_stats()
    return PipelineResult(task, code, review, attempts)


def project_management(prompt: str, max_retries: int = MAX_REPAIRS) -> tuple[str, str, str]:
    """Compatibility wrapper returning the latest candidate and its QA verdict."""
    result = project_management_with_attempts(prompt, max_retries)
    return result.task.as_markdown(), result.code, result.review.as_text()
