import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from tempfile import NamedTemporaryFile

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_summarize():
    log_lines = [
        'INFO:root:This is an info message',
        'WARNING:root:This is a warning message',
        'ERROR:root:This is an error message'
    ]
    summary = candidate_module.summarize(log_lines)
    assert summary == {'': 0, 'ERROR': 1, 'INFO': 1, 'WARNING': 1}

def test_summarize_empty_input():
    log_lines = []
    summary = candidate_module.summarize(log_lines)
    assert summary == {'': 0}

def test_cli_valid_case():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.write('INFO:root:This is an info message\n')
        f.write('WARNING:root:This is a warning message\n')
        f.flush()
        subprocess.run([sys.executable, CANDIDATE_PATH], stdin=f.file, capture_output=True)
        with open(f.name) as f:
            output = json.load(f)
    assert output == {'': 0, 'INFO': 1, 'WARNING': 1}

def test_cli_invalid_case():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.write('This is not a valid log message\n')
        f.flush()
        subprocess.run([sys.executable, CANDIDATE_PATH], stdin=f.file, capture_output=True)
        with open(f.name) as f:
            output = json.load(f)
    assert output == {'': 1}

def test_cli_empty_input():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        subprocess.run([sys.executable, CANDIDATE_PATH], stdin=f.file, capture_output=True)
        with open(f.name) as f:
            output = json.load(f)
    assert output == {'': 0}