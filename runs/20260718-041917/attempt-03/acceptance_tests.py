import os
import sys
from pathlib import Path
import tempfile
import json
import importlib.util
import subprocess

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    text = "Hello, World!\nThis is a test."
    result = candidate_module.analyze_text(text)
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'words' in result
    assert 'characters' in result
    assert 'word_frequencies' in result

def test_analyze_empty_text():
    text = ""
    result = candidate_module.analyze_text(text)
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'words' in result
    assert 'characters' in result
    assert 'word_frequencies' in result

def test_cli_valid_case():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "Hello, World!\nThis is a test."
        file.write(text)
        file.flush()
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH, file.name], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate(input=text.encode('utf-8'), timeout=1)
        result = json.loads(output.decode('utf-8'))
        assert isinstance(result, dict)
        assert 'lines' in result
        assert 'words' in result
        assert 'characters' in result
        assert 'word_frequencies' in result

def test_cli_invalid_case():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "Hello, World!\nThis is a test."
        file.write(text)
        file.flush()
        process = subprocess.Popen([sys.executable, CANDIDATE_PATH, file.name], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate(input=b"Invalid input", timeout=1)
        assert b"Error:" in error

if __name__ == '__main__':
    test_analyze_text()
    test_analyze_empty_text()
    test_cli_valid_case()
    test_cli_invalid_case()