"""Checked-in runtime settings for the fast local generation pipeline.

Edit this file on the machine that runs Ollama.  These are deliberately not
environment variables: the pipeline should run predictably from its source.
"""

PRIMARY_MODEL = "deepseek-api:deepseek-chat"
# Use local DeepSeek for reasoning/review; keep coding on the API model.
PLANNER_MODEL = "deepseek-r1:8b"
CODER_MODEL = PRIMARY_MODEL
QA_MODEL = PLANNER_MODEL

# Offline fallback only. It is not selected when DEEPSEEK_API_KEY is present.
LOCAL_CODER_FALLBACK_MODEL = "qwen2.5-coder:14b"

MODEL_KEEP_ALIVE = "30m"
# A second focused repair lets the coder address the full review list without
# adding another independent QA subsystem.  On the target GPU this is a small
# latency trade for materially better first-pass completion.
MAX_REPAIRS = 2
STARTUP_GRACE_SECONDS = 1.0
ACCEPTANCE_TEST_TIMEOUT_SECONDS = 5.0

# Default loop: plan, generate, deterministic checks, executable acceptance
# evidence, review, and focused repairs.
ENABLE_PLANNING = True
ENABLE_LLM_REVIEW = True
ENABLE_ACCEPTANCE_TESTS = True
ESCALATION_MODEL = ""
# DeepSeek is an optional, bounded escalation role.  It is never used for
# planning, default generation, acceptance generation, or trusted QA.
DEEPSEEK_ESCALATION_ENABLED = False
DEEPSEEK_ESCALATION_MODEL = "deepseek-chat"
DEEPSEEK_MAX_CALLS_PER_RUN = 1
