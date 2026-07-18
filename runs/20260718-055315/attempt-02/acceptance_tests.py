import os
import sys
from pathlib import Path
import tempfile
import importlib.util
import json

# Load candidate from file
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text_valid():
    text = "This is a sample text with multiple lines.\nAnd another line."
    stats = candidate_module.analyze_text(text)
    assert stats == {
        'lines': 2,
        'words': 8,
        'characters': 46,
        'word_frequencies': {'this': 1, 'is': 1, 'a': 1, 'sample': 1, 'text': 1, 'with': 1, 'multiple': 1, 'lines': 1, 'and': 1, 'another': 1}
    }

def test_analyze_text_empty():
    text = ""
    stats = candidate_module.analyze_text(text)
    assert stats == {
        'lines': 0,
        'words': 0,
        'characters': 0,
        'word_frequencies': {}
    }

def test_analyze_text_none():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = None
        stats = candidate_module.analyze_text(text)
        assert stats == {
            'lines': 0,
            'words': 0,
            'characters': 0,
            'word_frequencies': {}
        }

def test_cli_valid():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "This is a sample text with multiple lines.\nAnd another line."
        file.write(text)
        file.flush()
        sys.argv = ['text_stats.py', str(file.name)]
        candidate_module.main()
        stats = json.load(sys.stdin)
        assert stats == {
            'lines': 2,
            'words': 8,
            'characters': 46,
            'word_frequencies': {'this': 1, 'is': 1, 'a': 1, 'sample': 1, 'text': 1, 'with': 1, 'multiple': 1, 'lines': 1, 'and': 1, 'another': 1}
        }

def test_cli_invalid():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "This is a sample text with multiple lines.\nAnd another line."
        file.write(text)
        file.flush()
        sys.argv = ['text_stats.py']
        candidate_module.main()
        assert False, "Expected usage message"

def test_cli_empty_file():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = ""
        file.write(text)
        file.flush()
        sys.argv = ['text_stats.py', str(file.name)]
        candidate_module.main()
        stats = json.load(sys.stdin)
        assert stats == {
            'lines': 0,
            'words': 0,
            'characters': 0,
            'word_frequencies': {}
        }

def test_cli_non_existent_file():
    sys.argv = ['text_stats.py', 'non_existent_file.txt']
    candidate_module.main()
    assert False, "Expected error message"

test_analyze_text_valid()
test_analyze_text_empty()
test_analyze_text_none()
test_cli_valid()
test_cli_invalid()
test_cli_empty_file()
test_cli_non_existent_file()