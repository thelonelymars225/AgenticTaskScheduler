import os
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import sys

# Load the candidate module
spec = importlib.util.spec_from_file_location("text_stats", os.environ['CANDIDATE_PATH'])
text_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(text_stats)

def test_analyze_text_empty_string():
    result = text_stats.analyze_text("")
    assert result == {
        'lines': 0,
        'words': 0,
        'characters': 0,
        'word_frequencies': {}
    }

def test_analyze_text_single_line():
    text = "Hello, World!"
    result = text_stats.analyze_text(text)
    assert result['lines'] == 1
    assert result['words'] == 2
    assert result['characters'] == len(text)
    word_freqs = result['word_frequencies']
    assert list(word_freqs.keys()) == ['hello', 'world']

def test_analyze_text_multiple_lines():
    text = "Line 1\nLine 2\nLine 3"
    result = text_stats.analyze_text(text)
    assert result['lines'] == 3
    assert result['words'] == 6
    assert result['characters'] == len(text)

def test_analyze_text_word_frequencies():
    text = "apple apple banana orange orange"
    result = text_stats.analyze_text(text)
    word_freqs = result['word_frequencies']
    assert list(word_freqs.keys()) == ['apple', 'banana', 'orange']
    assert word_freqs['apple'] == 2
    assert word_freqs['banana'] == 1
    assert word_freqs['orange'] == 2

def test_cli_valid_file():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        text = "Hello, World!\nThis is a test."
        tmp.write(text)
        tmp.flush()
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], tmp.name], capture_output=True, text=True)
        output = json.loads(result.stdout)
        assert output == {
            'lines': 2,
            'words': 6,
            'characters': len(text),
            'word_frequencies': {'hello': 1, 'world': 1, 'this': 1, 'is': 1, 'a': 1, 'test': 1}
        }

def test_cli_invalid_file():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        text = "Invalid UTF-8"
        tmp.write(text.encode('latin1'))
        tmp.flush()
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], tmp.name], capture_output=True, text=True)
        output = json.loads(result.stdout)
        assert output == {
            'lines': 0,
            'words': 0,
            'characters': 0,
            'word_frequencies': {}
        }

def test_cli_non_existent_file():
    result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], 'non_existent_file.txt'], capture_output=True, text=True)
    output = json.loads(result.stdout)
    assert output == {
        'lines': 0,
        'words': 0,
        'characters': 0,
        'word_frequencies': {}
    }

def test_cli_permission_denied():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        text = "Hello, World!"
        tmp.write(text)
        tmp.flush()
        os.chmod(tmp.name, 0o000)
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], tmp.name], capture_output=True, text=True)
        output = json.loads(result.stdout)
        assert output == {
            'lines': 1,
            'words': 2,
            'characters': len(text),
            'word_frequencies': {'hello': 1, 'world': 1}
        }

def test_cli_invalid_utf8():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
        text = "Invalid UTF-8"
        tmp.write(text.encode('latin1'))
        tmp.flush()
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], tmp.name], capture_output=True, text=True)
        output = json.loads(result.stdout)
        assert output == {
            'lines': 0,
            'words': 0,
            'characters': 0,
            'word_frequencies': {}
        }