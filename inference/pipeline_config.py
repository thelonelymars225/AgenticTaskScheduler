"""Checked-in runtime settings for the fast local generation pipeline.

Edit this file on the machine that runs Ollama.  These are deliberately not
environment variables: the pipeline should run predictably from its source.
"""

PRIMARY_MODEL = "qwen2.5-coder:14b"
# Use different roles so the reviewer is less likely to repeat the coder's
# blind spots. These models are expected to be available on the runtime PC.
PLANNER_MODEL = "llama3.1:8b"
CODER_MODEL = PRIMARY_MODEL
QA_MODEL = "deepseek-r1:8b"

MODEL_KEEP_ALIVE = "30m"
MAX_REPAIRS = 2
STARTUP_GRACE_SECONDS = 1.0
ACCEPTANCE_TEST_TIMEOUT_SECONDS = 5.0

# Quality-first default: plan the task, generate, review against the plan,
# then make targeted repairs. Disable these only for throwaway generations.
ENABLE_PLANNING = True
ENABLE_LLM_REVIEW = True
ENABLE_ACCEPTANCE_TESTS = True
ESCALATION_MODEL = ""
