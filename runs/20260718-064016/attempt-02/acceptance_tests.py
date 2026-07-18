import importlib.util
import os
import json
from pathlib import Path
import tempfile
import subprocess

# Load the candidate module
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    # Test a valid string input
    text = "This is a sample text with multiple lines."
    result = candidate_module.analyze_text(text)
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'characters' in result
    assert 'words' in result
    assert 'frequency' in result

def test_analyze_file():
    # Create a temporary file with some text
    temp_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8')
    text = "This is a sample text with multiple lines."
    temp_file.write(text)
    temp_file.flush()

    # Analyze the file
    result = candidate_module.analyze_file(temp_file.name)

    # Check the result
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'characters' in result
    assert 'words' in result
    assert 'frequency' in result

def test_invalid_input():
    # Test with None input
    try:
        candidate_module.analyze_text(None)
        assert False, "Expected TypeError"
    except TypeError as e:
        assert str(e) == "Input must be a string"

    # Test with non-string input
    try:
        candidate_module.analyze_text(123)
        assert False, "Expected TypeError"
    except TypeError as e:
        assert str(e) == "Input must be a string"

def test_cli():
    # Create a temporary file with some text
    temp_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8')
    text = "This is a sample text with multiple lines."
    temp_file.write(text)
    temp_file.flush()

    # Run the CLI
    process = subprocess.Popen(['python', os.environ['CANDIDATE_PATH'], temp_file.name],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check the output
    output, error = process.communicate()
    assert b'{"lines":' in output

    # Check the exit code
    if process.returncode != 0:
        print(f"Error: Unexpected return code {process.returncode}")
        raise AssertionError()

def test_cli_invalid_input():
    # Run the CLI with an invalid input path
    process = subprocess.Popen(['python', os.environ['CANDIDATE_PATH'], 'invalid_path'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check the output
    output, error = process.communicate()
    assert b"Error: No such file:" in error

    # Check the exit code
    if process.returncode != 2:
        print(f"Error: Unexpected return code {process.returncode}")
        raise AssertionError()

if __name__ == "__main__":
    test_analyze_text()
    test_analyze_file()
    test_invalid_input()
    test_cli()
    test_cli_invalid_input()