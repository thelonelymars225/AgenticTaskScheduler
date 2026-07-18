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
        'INFO: This is an info message',
        'WARNING: This is a warning message',
        'ERROR: This is an error message',
        '',
        'INFO: Another info message'
    ]
    expected_output = {
        '': 1,
        'INFO': 2,
        'WARNING': 1,
        'ERROR': 1
    }
    result = candidate_module.summarize(log_lines)
    assert result == expected_output

def test_main():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        log_lines = [
            'INFO: This is an info message',
            'WARNING: This is a warning message',
            'ERROR: This is an error message',
            '',
            'INFO: Another info message'
        ]
        for line in log_lines:
            tmp.write(line + '\n')
        tmp.flush()
        
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=tmp.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        result = json.loads(output.decode('utf-8'))
        assert result == {
            '': 1,
            'INFO': 2,
            'WARNING': 1,
            'ERROR': 1
        }

def test_empty_input():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        tmp.flush()
        
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=tmp.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        result = json.loads(output.decode('utf-8'))
        assert result == {'': 0}

def test_invalid_input():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        log_lines = [
            'INFO: This is an info message',
            'WARNING: This is a warning message',
            'ERROR: This is an error message',
            '',
            'INFO: Another info message'
        ]
        for line in log_lines:
            tmp.write(line + '\n')
        tmp.flush()
        
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH], stdin=tmp.file, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        assert output == b'1\n'

if __name__ == '__main__':
    test_summarize()
    test_main()
    test_empty_input()
    test_invalid_input()