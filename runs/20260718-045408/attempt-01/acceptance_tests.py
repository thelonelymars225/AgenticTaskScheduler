import sys
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
from unittest.mock import patch

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_summarize():
    log_lines = [
        "INFO: This is an info message",
        "WARNING: This is a warning message",
        "ERROR: This is an error message",
        "",
        "INFO: Another info message"
    ]

    summary = candidate_module.summarize(log_lines)
    assert summary == {'INFO': 2, 'WARNING': 1, 'ERROR': 1, '': 1}

def test_main_valid():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.write("INFO: This is an info message\n")
        f.write("WARNING: This is a warning message\n")
        f.flush()

        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=f.file)
        output, _ = process.communicate()
        assert json.loads(output.decode('utf-8')) == {'INFO': 1, 'WARNING': 1}

def test_main_invalid():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.write("This is not a valid log line\n")
        f.flush()

        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=f.file)
        output, _ = process.communicate()
        assert json.loads(output.decode('utf-8')) == {'': 1}

def test_main_empty_input():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.flush()

        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=f.file)
        output, _ = process.communicate()
        assert json.loads(output.decode('utf-8')) == {}