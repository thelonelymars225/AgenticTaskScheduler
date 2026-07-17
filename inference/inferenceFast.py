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

from timer import Timer

CLIENT = ollama.Client()
PRIMARY_MODEL = os.getenv("ATS_PRIMARY_MODEL", "qwen2.5-coder:14b")
PLANNER_MODEL = os.getenv("ATS_PLANNER_MODEL", PRIMARY_MODEL)
CODER_MODEL = os.getenv("ATS_CODER_MODEL", PRIMARY_MODEL)
QA_MODEL = os.getenv("ATS_QA_MODEL", PRIMARY_MODEL)
ESCALATION_MODEL = os.getenv("ATS_ESCALATION_MODEL", "qwen2.5-coder:32b")
KEEP_ALIVE = os.getenv("ATS_MODEL_KEEP_ALIVE", "30m")
MAX_REPAIRS = max(0, int(os.getenv("ATS_MAX_REPAIRS", "2")))
STARTUP_GRACE = max(1.0, float(os.getenv("ATS_STARTUP_GRACE_SECONDS", "3")))
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


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
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
    issues = _as_list(payload.get("issues"))
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
                "Complexity must be simple, medium, complex, or very_complex. Create the smallest design that works. "
                "Acceptance tests must be concrete and observable. Do not over-engineer."
            )},
            {"role": "user", "content": prompt},
        ],
        json_output=True,
        num_predict=1500,
    )
    return _parse_plan_payload(text)


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
                "The program must compile and start. When AGENT_SMOKE_TEST=1, run a safe non-interactive "
                "self-check and exit 0 rather than blocking. "
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
                "reported failure. Preserve working behavior and the AGENT_SMOKE_TEST=1 non-blocking path."
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


def quality_review(code: str, task: TaskPlan) -> ReviewResult:
    text = _chat(
        QA_MODEL,
        [
            {"role": "system", "content": (
                "Return valid JSON only: {\"verdict\":\"PASS\"|\"FAIL\",\"issues\":[\"specific issue\"]}. "
                "PASS only if every required behavior and acceptance test is implemented. Ignore optional improvements."
            )},
            {"role": "user", "content": f"{task.as_markdown()}\n\nCode:\n```python\n{code}\n```"},
        ],
        json_output=True,
        num_predict=1200,
        temperature=0.0,
    )
    return _parse_review_payload(text)


def project_management(prompt: str, max_retries: int = MAX_REPAIRS) -> tuple[str, str, str]:
    max_retries = max(0, min(max_retries, MAX_REPAIRS))
    Timer.reset_all()
    with Timer("pipeline.analyze"):
        task = analyze_task(prompt)
    with Timer("pipeline.generate"):
        code = write_code(prompt, task)

    failures: list[str] = []
    review = ReviewResult(False, ["Pipeline did not complete."])
    for attempt in range(max_retries + 1):
        with Timer(f"pipeline.validate.{attempt + 1}"):
            validation = validate_code(code, task)
        if validation.passed:
            with Timer(f"pipeline.review.{attempt + 1}"):
                review = quality_review(code, task)
            if review.passed:
                Timer.print_stats()
                return task.as_markdown(), code, review.as_text()
            failures.extend(review.issues)
        else:
            review = ReviewResult(False, validation.failures)
            failures.extend(validation.failures)
        if attempt < max_retries:
            with Timer(f"pipeline.repair.{attempt + 1}"):
                code = repair_code(code, task, failures)

    if ESCALATION_MODEL and ESCALATION_MODEL != CODER_MODEL:
        with Timer("pipeline.escalate"):
            code = write_code(prompt, task, ESCALATION_MODEL, failures)
        validation = validate_code(code, task)
        review = quality_review(code, task) if validation.passed else ReviewResult(False, validation.failures)

    Timer.print_stats()
    return task.as_markdown(), code, review.as_text()
