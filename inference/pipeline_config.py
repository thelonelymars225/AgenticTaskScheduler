"""Checked-in runtime settings for the fast local generation pipeline.

Edit this file on the machine that runs Ollama.  These are deliberately not
environment variables: the pipeline should run predictably from its source.
"""

PRIMARY_MODEL = "qwen2.5-coder:14b"
PLANNER_MODEL = PRIMARY_MODEL
CODER_MODEL = PRIMARY_MODEL
QA_MODEL = PRIMARY_MODEL

MODEL_KEEP_ALIVE = "30m"
MAX_REPAIRS = 1
STARTUP_GRACE_SECONDS = 1.0

# Keep the fast path to a single model call. Enable these only when a task
# benefits from the additional latency and model work.
ENABLE_PLANNING = False
ENABLE_LLM_REVIEW = False
ESCALATION_MODEL = ""
