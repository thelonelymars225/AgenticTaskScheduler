import json
import os
import sys
import importlib.util
from pathlib import Path
from tempfile import NamedTemporaryFile
from io import StringIO
import subprocess

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_summarize():
    log_lines = [
        'INFO: This is an info message',
        'WARNING: This is a warning message',
        'ERROR: This is an error message'
    ]
    summary = candidate_module.summarize(log_lines)
    assert summary == {'': 1, 'INFO': 1, 'WARNING': 1, 'ERROR': 1}

def test_summarize_empty_input():
    log_lines = []
    summary = candidate_module.summarize(log_lines)
    assert summary == {'': len(log_lines)}

def test_cli_valid_case():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.write('INFO: This is an info message\n')
        f.write('WARNING: This is a warning message\n')
        f.flush()
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=f.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        summary = json.loads(output.decode('utf-8'))
        assert summary == {'': 2, 'INFO': 1, 'WARNING': 1}

def test_cli_invalid_case():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.write('This is not a valid log message\n')
        f.flush()
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=f.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        summary = json.loads(output.decode('utf-8'))
        assert summary == {'': 1}

def test_cli_empty_input():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.flush()
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=f.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        summary = json.loads(output.decode('utf-8'))
        assert summary == {'': 0}