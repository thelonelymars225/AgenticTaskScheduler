"""
Local-only inference pipeline. No API calls.
For visual prompts (GUI/game), runs the app, takes a screenshot,
and uses a local vision model for visual QA.
"""

import ollama
from timer import Timer
import subprocess
import tempfile
import os
import re
import time
import signal

ollama_client = ollama.Client()

# Pre-warm models
for m in ['llava:7b', 'deepseek-r1:8b', 'llama3.1:8b', 'qwen2.5-coder:14b']:
    ollama_client.generate(model=m, prompt='', keep_alive='60m', options={'temperature': 0.1})


# ── Helpers ────────────────────────────────────────────────────────

def _extract_spec(text):
    """Extract the ## Specification section from business analysis output."""
    m = re.search(r'## Specification\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    return m.group(1).strip() if m else text


def _strip_code_blocks(text):
    """Strip markdown code fences, returning only the Python code."""
    if not text:
        return ""
    blocks = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
    if blocks:
        return blocks[-1].strip()
    return text.strip()


# ── Visual prompt detection ───────────────────────────────────────

def _is_visual_prompt(prompt: str) -> bool:
    """Detect if a prompt is likely a GUI/game that needs visual QA."""
    keywords = [
        'gui', 'game', 'tkinter', 'pygame', 'window', 'canvas',
        'ui', 'interface', 'app', 'dash', 'plot', 'chart',
        'snake', 'calculator', 'paint', 'editor', 'player',
        'screen', 'display', 'button', 'menu', 'dialog',
        'graphical', 'widget', 'frame', 'label', 'entry',
    ]
    p = prompt.lower()
    return any(k in p for k in keywords)


# ── Screenshot capture ────────────────────────────────────────────

def _capture_screenshot(output_path: str, delay: float = 2.0) -> bool:
    """Capture a screenshot of the running app using importlib (no extra deps)."""
    try:
        # Use mss for fast screen capture (install: pip install mss)
        import mss
        with mss.mss() as sct:
            time.sleep(delay)
            monitor = sct.monitors[1]  # primary monitor
            sct.shot(output=output_path)
        return True
    except ImportError:
        pass

    # Fallback: use scrot (Linux) or screencapture (macOS)
    try:
        time.sleep(delay)
        if os.name == 'posix':
            if os.system('which scrot > /dev/null 2>&1') == 0:
                subprocess.run(['scrot', output_path], capture_output=True, timeout=5)
                return os.path.exists(output_path)
            elif os.system('which screencapture > /dev/null 2>&1') == 0:
                subprocess.run(['screencapture', output_path], capture_output=True, timeout=5)
                return os.path.exists(output_path)
    except Exception:
        pass

    return False


# ── Visual QA (local vision model) ────────────────────────────────

def _visual_qa(spec: str, plan: str, screenshot_path: str) -> str:
    """Use local vision model (llava) to analyze the screenshot against the spec."""
    with open(screenshot_path, 'rb') as f:
        import base64
        img_b64 = base64.b64encode(f.read()).decode()

    response = ollama_client.chat(
        model="llava:7b",
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a QA engineer reviewing a GUI application by looking at a screenshot.\n"
                    "Compare what you SEE in the screenshot against the specification below.\n\n"
                    f"## Specification\n{spec}\n\n"
                    f"## Plan\n{plan}\n\n"
                    "Check for:\n"
                    "1. Missing UI elements (buttons, labels, canvas, score display)\n"
                    "2. Wrong layout (elements overlapping, wrong positions, bad sizing)\n"
                    "3. Visual bugs (wrong colors, missing text, broken rendering)\n"
                    "4. Missing features that should be visible\n\n"
                    "Be specific about what looks wrong.\n"
                    "If everything looks correct and matches the spec, end with: No bugs found."
                ),
            }
        ],
        options={'temperature': 0.2},
    )
    return response["message"]["content"]


# ── Stage 1: Spec & Plan ──────────────────────────────────────────

def business_analysis(prompt):
    """Expand a vague user prompt into a detailed specification + complexity score."""
    response = ollama_client.chat(
        model="llama3.1:8b",
        messages=[
            {"role": "system", "content": "You are a senior software architect. The user gave a bare-minimum request. "
             "Your job is to OVER-ENGINEER it — add everything a real production app needs.\n\n"
             "Output exactly this format:\n"
             "## Specification\n"
             "List every feature the code must have. ALWAYS proactively add:\n"
             "- **Error handling** for every failure point\n"
             "- **Input validation** (empty, out-of-range, type mismatches)\n"
             "- **Edge cases** (boundaries, rapid input, concurrent actions, zero states)\n"
             "- **User experience** (loading states, confirmations, undo, feedback messages)\n"
             "- **Configurability** (constants at top, settings, adjustable parameters)\n"
             "- **State management** (save/restore state, persistence if applicable)\n"
             "- **Graceful degradation** (what happens when something fails)\n\n"
             "## Analysis\n"
             "Complexity assessment.\n\n"
             "COMPLEXITY: X\n"
             "X: 2000 (trivial), 4000 (simple), 8000 (medium), 12000 (complex), 16000 (very complex)"},
            {"role": "user", "content": prompt}
        ],
        options={'temperature': 0.2, 'num_predict': 2000}
    )
    return response["message"]["content"]


def create_plan(spec, analysis):
    """Produce a detailed architectural plan from the spec (not the raw prompt)."""
    response = ollama_client.chat(
        model="llama3.1:8b",
        messages=[
            {"role": "system", "content": "You are a senior software architect. Design a detailed implementation plan.\n"
             "Output ONLY a structured plan with:\n"
             "## Architecture\n- Overall structure, key classes, their responsibilities\n"
             "## Components\n- List every class/function needed, with signatures\n"
             "## Data Flow\n- How data moves between components\n"
             "## Edge Cases\n- What edge cases must be handled\n"
             "## Implementation Order\n- Step-by-step build order\n\n"
             "Do NOT write any code — only the plan."},
            {"role": "user", "content": f"## Specification\n{spec}\n\n## Analysis\n{analysis}\n\nCreate a detailed implementation plan following the spec exactly."}
        ],
        options={'temperature': 0.3, 'num_predict': 2000}
    )
    return response["message"]["content"]


# ── Stage 2: Code generation ──────────────────────────────────────

def write_code(spec, plan, char_limit, qa_history=None):
    """Write code locally via qwen2.5-coder:14b."""
    history_section = ""
    if qa_history:
        history_section = "\n## Issues to Avoid (from previous attempts)\n" + "\n---\n".join(qa_history)

    response = ollama_client.chat(
        model="qwen2.5-coder:14b",
        messages=[
            {"role": "system", "content": "You are a senior software engineer implementing a detailed plan. "
             "Write EXHAUSTIVE, production-quality Python code. "
             "EVERY class and function MUST have a docstring explaining what it does. "
             "Include type hints on ALL function signatures and class attributes. "
             "Add inline comments for non-obvious logic. "
             "Declare all configuration as named constants at the file top. "
             "Implement error handling for EVERY failure path. "
             "Do NOT abbreviate or skip any component — write the FULL implementation. "
             f"Maximum {char_limit} characters for the ENTIRE response."},
            {"role": "user", "content": f"## Specification\n{spec}\n\n## Implementation Plan\n{plan}{history_section}\n\nWrite the COMPLETE Python code. Every class, every method, fully implemented with docstrings and type hints. Do NOT abbreviate or skip."}
        ],
        options={'temperature': 0.1}
    )
    return _strip_code_blocks(response["message"]["content"])


def fix_code(existing_code, feedback, spec, plan, char_limit, qa_history=None):
    """Fix code based on QA feedback, with history to prevent repeated bugs."""
    history_section = ""
    if qa_history and len(qa_history) > 1:
        history_section = "\n## Previously Reported Bugs (now fixed)\n" + "\n---\n".join(qa_history[:-1])

    response = ollama_client.chat(
        model="qwen2.5-coder:14b",
        messages=[
            {"role": "system", "content": "You are a senior software engineer. Fix ALL bugs listed below and expand the code. "
             "Add docstrings to any class/method that lacks them. Add type hints everywhere. "
             "Add comments for complex logic. Handle ALL error paths. "
             "Follow the original spec and plan. Return the COMPLETE corrected file — do NOT truncate."},
            {"role": "user", "content": f"## Specification\n{spec}\n\n## Original Plan\n{plan}\n\n## Current Bugs to Fix\n{feedback}{history_section}\n\n## Current Code\n```python\n{existing_code}\n```\n\nRewrite the ENTIRE file with all bugs fixed. Expand and complete any missing parts."}
        ],
        options={'temperature': 0.1}
    )
    return _strip_code_blocks(response["message"]["content"])


# ── Validation ─────────────────────────────────────────────────────

def validate_syntax(code):
    try:
        compile(code, "<string>", "exec")
        return ""
    except SyntaxError as e:
        return f"SyntaxError: {e}"


def runtime_check(code, timeout=5):
    """Run the code briefly to catch crashes."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        try:
            result = subprocess.run(
                ['uv', 'run', 'python3', f.name],
                capture_output=True, text=True, timeout=timeout
            )
            if result.returncode != 0:
                err = result.stderr.strip()
                if not any(kw in err for kw in ['mainloop', 'main loop', 'pygame']):
                    return err[:600]
            return ""
        except subprocess.TimeoutExpired:
            return ""
        except FileNotFoundError:
            return ""
        finally:
            os.unlink(f.name)


def has_no_bugs(feedback):
    indicators = [
        "no bugs found", "no bug found", "looks good", "looks correct",
        "no issues found", "code is correct", "code looks fine",
        "no problems found", "passes all checks", "all good",
        "i don't see any bugs", "no errors found",
    ]
    return any(i in feedback.lower() for i in indicators)


# ── Stage 3: QA (text) ────────────────────────────────────────────

def qa(code, spec, plan, qa_history=None):
    """Three-stage text QA: syntax → runtime → deep review."""

    syntax_err = validate_syntax(code)
    if syntax_err:
        return f"[SYNTAX ERROR]\n{syntax_err}"

    runtime_err = runtime_check(code)
    if runtime_err:
        return f"[RUNTIME ERROR]\n{runtime_err}"

    history_section = ""
    if qa_history:
        history_section = "\n\n## Previously Reported Issues (check if these are truly fixed)\n" + "\n".join(f"- {h}" for h in qa_history)

    response = ollama_client.chat(
        model="deepseek-r1:8b",
        messages=[
            {"role": "system", "content": "You are a senior QA engineer. Compare the code against the specification AND the plan.\n"
             "Check for:\n"
             "1. CRITICAL: Every method called MUST exist on that class.\n"
             "2. Missing features from the specification\n"
             "3. Components from the plan that are missing or incomplete\n"
             "4. Logic bugs (infinite loops, wrong conditions, off-by-one)\n"
             "5. Runtime crashes (NoneType, index errors, division by zero)\n"
             "6. UX / output issues (nothing displayed, GUI frozen, bad layout)\n\n"
             "IMPORTANT: Do NOT repeat issues from the 'Previously Reported Issues' list "
             "unless they are STILL present in the current code.\n\n"
             "Be specific — mention exact class names, method names, and line numbers.\n"
             "If the code fully implements the specification following the plan with no bugs, end with: No bugs found."},
            {"role": "user", "content": f"## Specification\n{spec}\n\n## Plan\n{plan}\n\n## Code\n```python\n{code}\n```{history_section}"}
        ],
        options={'temperature': 0.2}
    )
    return response["message"]["content"]


# ── Stage 4: Visual QA (for GUI/game prompts) ─────────────────────

def visual_qa(code, spec, plan, screenshot_path=None):
    """Run the code, screenshot it, and analyze with a local vision model."""
    # Step 1: Run the code in background
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        proc = subprocess.Popen(
            ['uv', 'run', 'python3', temp_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )

        # Step 2: Wait for app to render, then screenshot
        screenshot_path = screenshot_path or "/tmp/visual_qa_screenshot.png"
        captured = _capture_screenshot(screenshot_path, delay=3.0)

        # Kill the app
        try:
            if hasattr(os, 'setsid'):
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
            proc.wait()

        if not captured:
            return "[VISUAL QA ERROR]\nCould not capture screenshot."

        # Step 3: Vision model checks the screenshot
        vision_feedback = _visual_qa(spec, plan, screenshot_path)
        return vision_feedback

    except Exception as e:
        return f"[VISUAL QA ERROR]\n{str(e)}"
    finally:
        try:
            os.unlink(temp_path)
        except Exception:
            pass


# ── Pipeline ──────────────────────────────────────────────────────

def project_management(prompt, max_retries=5):
    visual = _is_visual_prompt(prompt)
    print(f"{'🖥️  Visual' if visual else '📄  Text'} prompt detected")

    with Timer("pipeline.business_analysis"):
        business_analysis_result = business_analysis(prompt)

    spec = _extract_spec(business_analysis_result)

    match = re.search(r'COMPLEXITY:\s*(\d+)', business_analysis_result, re.IGNORECASE)
    char_limit = int(match.group(1)) if match else 8000
    char_limit = {2000: 4000, 4000: 8000, 8000: 12000, 12000: 16000}.get(char_limit, char_limit)
    char_limit *= 15

    with Timer("pipeline.create_plan"):
        plan = create_plan(spec, business_analysis_result)

    with Timer("pipeline.write_code"):
        code = write_code(spec, plan, char_limit)

    qa_history = []

    # Visual prompts: cap at 2 retries. Fix model can't see screenshots,
    # so more attempts just wastes time on blind fixes.
    visual_max = 2 if visual else max_retries

    for attempt in range(visual_max if visual else max_retries):
        if not code.strip():
            print(f"⚠️  Code empty (attempt {attempt + 1}), retrying...")
            with Timer(f"pipeline.write_code (retry {attempt + 1})"):
                code = write_code(spec, plan, char_limit, qa_history)
            continue

        with Timer(f"pipeline.qa (attempt {attempt + 1})"):
            if visual:
                feedback = visual_qa(code, spec, plan)
            else:
                feedback = qa(code, spec, plan, qa_history)

        if has_no_bugs(feedback):
            with Timer("pipeline.validate"):
                syntax_err = validate_syntax(code)
            if not syntax_err:
                Timer.print_stats()
                return business_analysis_result, code, feedback

        qa_history.append(feedback)
        is_broken = feedback.startswith("[SYNTAX ERROR]") or feedback.startswith("[RUNTIME ERROR]") or feedback.startswith("[VISUAL QA ERROR]")

        if is_broken:
            print(f"⚠️  Code broken (attempt {attempt + 1}), regenerating from plan...")
            with Timer(f"pipeline.regenerate (attempt {attempt + 1})"):
                code = write_code(spec, plan, char_limit, qa_history)
        else:
            print(f"Issues found, fixing... (attempt {attempt + 1})")
            with Timer(f"pipeline.fix_code (attempt {attempt + 1})"):
                code = fix_code(code, feedback, spec, plan, char_limit, qa_history)

    Timer.print_stats()
    last_feedback = visual_qa(code, spec, plan) if visual else qa(code, spec, plan, qa_history)
    return business_analysis_result, code, last_feedback
