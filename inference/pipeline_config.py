"""Checked-in runtime settings for the fast local generation pipeline.

Edit this file on the machine that runs Ollama.  These are deliberately not
environment variables: the pipeline should run predictably from its source.
"""

PRIMARY_MODEL = "qwen2.5-coder:14b"
# The planner is lightweight; use the stable coder model for review so review
# and repair share a reliable structured-output implementation.
PLANNER_MODEL = "llama3.1:8b"
CODER_MODEL = PRIMARY_MODEL
QA_MODEL = PRIMARY_MODEL

MODEL_KEEP_ALIVE = "30m"
# A second focused repair lets the coder address the full review list without
# adding another independent QA subsystem.  On the target GPU this is a small
# latency trade for materially better first-pass completion.
MAX_REPAIRS = 2
STARTUP_GRACE_SECONDS = 1.0
ACCEPTANCE_TEST_TIMEOUT_SECONDS = 5.0

# Default loop: plan, generate, deterministic checks, review, one repair.
# Generated acceptance tests remain available for deliberate deep-QA runs.
ENABLE_PLANNING = True
ENABLE_LLM_REVIEW = True
ENABLE_ACCEPTANCE_TESTS = False
ESCALATION_MODEL = ""
