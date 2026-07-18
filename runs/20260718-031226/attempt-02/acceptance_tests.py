import importlib.util
import json
import os
import sys
from tempfile import NamedTemporaryFile
from pathlib import Path

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_summarize():
    # Test valid case
    log_lines = [
        "INFO: This is an info message",
        "DEBUG: This is a debug message",
        "WARNING: This is a warning message",
        "ERROR: This is an error message"
    ]
    expected_output = {
        '': 0,
        'DEBUG': 1,
        'ERROR': 1,
        'INFO': 1,
        'WARNING': 1
    }
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f:
        json.dump(candidate_module.summarize(log_lines), f)
        f.flush()
        actual_output = json.load(f)
        assert expected_output == actual_output

    # Test invalid case (empty input)
    log_lines = []
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f:
        json.dump(candidate_module.summarize(log_lines), f)
        f.flush()
        actual_output = json.load(f)
        assert {'': 0} == actual_output

def test_main():
    # Test valid case
    log_lines = [
        "INFO: This is an info message",
        "DEBUG: This is a debug message",
        "WARNING: This is a warning message",
        "ERROR: This is an error message"
    ]
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f:
        for line in log_lines:
            f.write(line + '\n')
            f.flush()
        sys.stdin = open(f.name, 'r')
        candidate_module.main()
        sys.stdin = sys.__stdin__

    # Test invalid case (empty input)
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f:
        f.close()  # Close the file to simulate empty input
        sys.stdin = open(f.name, 'r')
        try:
            candidate_module.main()
            assert False, "Expected an exception for empty input"
        except SystemExit:
            pass
        sys.stdin = sys.__stdin__

def test_main_cli():
    # Test valid case
    log_lines = [
        "INFO: This is an info message",
        "DEBUG: This is a debug message",
        "WARNING: This is a warning message",
        "ERROR: This is an error message"
    ]
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f:
        for line in log_lines:
            f.write(line + '\n')
            f.flush()
        sys.stdin = open(f.name, 'r')
        candidate_module.main()
        sys.stdin = sys.__stdin__

    # Test invalid case (empty input)
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f:
        f.close()  # Close the file to simulate empty input
        sys.stdin = open(f.name, 'r')
        try:
            candidate_module.main()
            assert False, "Expected an exception for empty input"
        except SystemExit:
            pass
        sys.stdin = sys.__stdin__

if __name__ == '__main__':
    test_summarize()
    test_main()
    test_main_cli()