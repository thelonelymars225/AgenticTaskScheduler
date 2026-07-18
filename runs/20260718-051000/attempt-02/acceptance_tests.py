import os
import sys
from pathlib import Path
import tempfile
import json
import importlib.util
import subprocess

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text_valid():
    text = "This is a sample text.\nIt has multiple lines."
    result = candidate_module.analyze_text(text)
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'words' in result
    assert 'characters' in result
    assert 'word_frequencies' in result

def test_analyze_text_empty():
    text = ""
    result = candidate_module.analyze_text(text)
    assert isinstance(result, dict)
    assert 'lines' in result and result['lines'] == 0
    assert 'words' in result and result['words'] == 0
    assert 'characters' in result and result['characters'] == 0
    assert 'word_frequencies' in result and result['word_frequencies'] == {}

def test_analyze_text_invalid_input():
    text = None
    try:
        candidate_module.analyze_text(text)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert str(e) == "Input must be a string"

def test_cli_valid_file():
    filename = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("This is a sample text.\nIt has multiple lines.")
    command = [sys.executable, os.environ['CANDIDATE_PATH'], filename]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)
    output, _ = process.communicate()
    result = json.loads(output.decode('utf-8'))
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'words' in result
    assert 'characters' in result
    assert 'word_frequencies' in result

def test_cli_invalid_file():
    filename = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("Invalid UTF-8 text")
    command = [sys.executable, os.environ['CANDIDATE_PATH'], filename]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)
    output, _ = process.communicate()
    assert "Error: File" in output.decode('utf-8')

if __name__ == '__main__':
    test_analyze_text_valid()
    test_analyze_text_empty()
    test_analyze_text_invalid_input()
    test_cli_valid_file()
    test_cli_invalid_file()