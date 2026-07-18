import importlib.util
import json
import os
import pathlib
import subprocess
import sys

# Load the candidate module from its path in the environment variable CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_summarize_valid():
    # Create a valid log with multiple levels and messages
    log_lines = [
        "DEBUG Message 1",
        "INFO Message 2",
        "WARNING Message 3",
        "ERROR Message 4",
        "CRITICAL Message 5"
    ]

    summary = candidate_module.summarize(log_lines)
    assert isinstance(summary, dict)
    assert set(summary.keys()) == {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    assert all(isinstance(count, int) for count in summary.values())

def test_summarize_invalid():
    # Create an invalid log with a non-string level and message
    log_lines = [
        "123 Message 1",
        "INFO Message 2"
    ]

    summary = candidate_module.summarize(log_lines)
    assert isinstance(summary, dict)
    assert set(summary.keys()) == {'INFO'}
    assert all(isinstance(count, int) for count in summary.values())

def test_summarize_empty():
    # Test summarizing an empty log
    summary = candidate_module.summarize([])
    assert isinstance(summary, dict)
    assert set(summary.keys()) == set()

def test_cli_valid_input():
    # Create a temporary file with valid input and invoke the CLI
    temp_file = pathlib.Path('temp.log')
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("DEBUG Message 1\nINFO Message 2\nWARNING Message 3")

    subprocess.run([sys.executable, os.environ['CANDIDATE_PATH']], input=temp_file.read_text(), capture_output=True)

    # Read the output JSON
    output = json.loads(subprocess.check_output([sys.executable, os.environ['CANDIDATE_PATH']]).decode('utf-8'))

    assert isinstance(output, dict)
    assert set(output.keys()) == {'DEBUG', 'INFO', 'WARNING'}
    assert all(isinstance(count, int) for count in output.values())

def test_cli_invalid_input():
    # Create a temporary file with invalid input and invoke the CLI
    temp_file = pathlib.Path('temp.log')
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("123 Message 1\nINFO Message 2")

    subprocess.run([sys.executable, os.environ['CANDIDATE_PATH']], input=temp_file.read_text(), capture_output=True)

    # Read the output JSON
    output = json.loads(subprocess.check_output([sys.executable, os.environ['CANDIDATE_PATH']]).decode('utf-8'))

    assert isinstance(output, dict)
    assert set(output.keys()) == {'INFO'}
    assert all(isinstance(count, int) for count in output.values())

def test_cli_empty_input():
    # Test invoking the CLI with empty input
    subprocess.run([sys.executable, os.environ['CANDIDATE_PATH']], capture_output=True)

    # Read the output JSON
    output = json.loads(subprocess.check_output([sys.executable, os.environ['CANDIDATE_PATH']]).decode('utf-8'))

    assert isinstance(output, dict)
    assert set(output.keys()) == set()

if __name__ == '__main__':
    test_summarize_valid()
    test_summarize_invalid()
    test_summarize_empty()
    test_cli_valid_input()
    test_cli_invalid_input()
    test_cli_empty_input()