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
    expected_output = {'': 0, 'INFO': 1, 'WARNING': 1, 'ERROR': 1}
    actual_output = candidate_module.summarize(log_lines)
    assert actual_output == expected_output

def test_summarize_empty_input():
    log_lines = []
    expected_output = {'': 3} # empty lines are counted as ''
    actual_output = candidate_module.summarize(log_lines)
    assert actual_output == expected_output

def test_cli_valid_case():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        log_lines = [
            'INFO:root:This is an info message',
            'WARNING:root:This is a warning message',
            'ERROR:root:This is an error message'
        ]
        for line in log_lines:
            tmp.write(line + '\n')
        tmp.flush()
        
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=tmp.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        actual_output = json.loads(output.decode('utf-8'))
        expected_output = {'': 0, 'INFO': 1, 'WARNING': 1, 'ERROR': 1}
        assert actual_output == expected_output

def test_cli_invalid_case():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        log_lines = [
            'INVALID:root:This is an invalid message'
        ]
        for line in log_lines:
            tmp.write(line + '\n')
        tmp.flush()
        
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=tmp.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        actual_output = json.loads(output.decode('utf-8'))
        expected_output = {'': 0, 'INVALID': 1}
        assert actual_output == expected_output

def test_cli_empty_input():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        for _ in range(3):
            tmp.write('\n')
        tmp.flush()
        
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=tmp.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        actual_output = json.loads(output.decode('utf-8'))
        expected_output = {'': 3}
        assert actual_output == expected_output