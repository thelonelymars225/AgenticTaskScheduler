import os
import sys
from pathlib import Path
import importlib.util
import tempfile
import json
import subprocess

# Load candidate from file
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text_empty():
    result = candidate_module.analyze_text("")
    assert result == {
        'lines': 0,
        'words': 0,
        'characters': 0,
        'word_frequencies': {}
    }

def test_analyze_text_valid():
    text = "This is a sample text.\nIt has multiple lines."
    result = candidate_module.analyze_text(text)
    assert result == {
        'lines': 2,
        'words': 6,
        'characters': len(text),
        'word_frequencies': {'this': 1, 'is': 1, 'a': 1, 'sample': 1, 'text': 1, 'it': 1, 'has': 1, 'multiple': 1, 'lines': 1}
    }

def test_analyze_text_invalid():
    text = "This is a sample text.\nIt has multiple lines."
    result = candidate_module.analyze_text(text + "\n")
    assert result == {
        'lines': 3,
        'words': 6,
        'characters': len(text) + 1,
        'word_frequencies': {'this': 1, 'is': 1, 'a': 1, 'sample': 1, 'text': 1, 'it': 1, 'has': 1, 'multiple': 1, 'lines': 2}
    }

def test_cli_valid():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "This is a sample text.\nIt has multiple lines."
        file.write(text)
        file.flush()
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], file.name], capture_output=True, text=True)
        json_result = json.loads(result.stdout)
        assert json_result == {
            'lines': 2,
            'words': 6,
            'characters': len(text),
            'word_frequencies': {'this': 1, 'is': 1, 'a': 1, 'sample': 1, 'text': 1, 'it': 1, 'has': 1, 'multiple': 1, 'lines': 1}
        }

def test_cli_invalid():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "This is a sample text.\nIt has multiple lines."
        file.write(text)
        file.flush()
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], file.name], capture_output=True, text=True)
        json_result = json.loads(result.stdout)
        assert json_result == {
            'lines': 3,
            'words': 6,
            'characters': len(text) + 1,
            'word_frequencies': {'this': 1, 'is': 1, 'a': 1, 'sample': 1, 'text': 1, 'it': 1, 'has': 1, 'multiple': 1, 'lines': 2}
        }

if __name__ == '__main__':
    test_analyze_text_empty()
    test_analyze_text_valid()
    test_analyze_text_invalid()
    test_cli_valid()
    test_cli_invalid()