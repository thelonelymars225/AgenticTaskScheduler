import importlib.util
import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

# Load the candidate module from its path in the environment variable CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_summarize():
    # Test a valid case with multiple log levels
    log_lines = [
        "DEBUG: This is a debug message",
        "INFO: This is an info message",
        "WARNING: This is a warning message",
        "ERROR: This is an error message",
        "CRITICAL: This is a critical message"
    ]
    expected_output = {
        'DEBUG': 1,
        'INFO': 1,
        'WARNING': 1,
        'ERROR': 1,
        'CRITICAL': 1
    }
    actual_output = candidate_module.summarize(log_lines)
    assert json.dumps(actual_output) == json.dumps(expected_output)

def test_summarize_empty_input():
    # Test an empty input with no log lines
    expected_output = {}
    actual_output = candidate_module.summarize([])
    assert json.dumps(actual_output) == json.dumps(expected_output)

def test_main_cli_valid_input():
    # Create a temporary file for the CLI to read from
    temp_file = NamedTemporaryFile(mode='w+', encoding='utf-8')
    log_lines = [
        "DEBUG: This is a debug message",
        "INFO: This is an info message",
        "WARNING: This is a warning message"
    ]
    temp_file.write('\n'.join(log_lines))
    temp_file.flush()

    # Run the CLI with the temporary file as input
    sys.stdin = open(temp_file.name, 'r', encoding='utf-8')
    candidate_module.main()
    actual_output = sys.stdout.getvalue().strip()
    expected_output = json.dumps({
        'DEBUG': 1,
        'INFO': 1,
        'WARNING': 1
    }, indent=4)
    assert actual_output == expected_output

def test_main_cli_invalid_input():
    # Create a temporary file for the CLI to read from with non-UTF-8 encoded input
    temp_file = NamedTemporaryFile(mode='w+', encoding='utf-8')
    log_lines = [
        "DEBUG: This is a debug message",
        "INFO: This is an info message",
        b'\xff'  # Non-UTF-8 encoded byte
    ]
    temp_file.write('\n'.join(log_lines))
    temp_file.flush()

    # Run the CLI with the temporary file as input
    sys.stdin = open(temp_file.name, 'r', encoding='utf-8')
    candidate_module.main()
    actual_output = sys.stdout.getvalue().strip()
    expected_output = json.dumps({
        'DEBUG': 1,
        'INFO': 1
    }, indent=4)
    assert actual_output == expected_output

def test_main_cli_empty_input():
    # Create a temporary file for the CLI to read from with no log lines
    temp_file = NamedTemporaryFile(mode='w+', encoding='utf-8')
    temp_file.write('')
    temp_file.flush()

    # Run the CLI with the temporary file as input
    sys.stdin = open(temp_file.name, 'r', encoding='utf-8')
    candidate_module.main()
    actual_output = sys.stdout.getvalue().strip()
    expected_output = json.dumps({}, indent=4)
    assert actual_output == expected_output

if __name__ == '__main__':
    test_summarize()
    test_summarize_empty_input()
    test_main_cli_valid_input()
    test_main_cli_invalid_input()
    test_main_cli_empty_input()