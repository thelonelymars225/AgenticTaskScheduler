import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
from collections import Counter

# Load the candidate module from its path in the environment variable CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("text_stats", os.environ['CANDIDATE_PATH'])
text_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(text_stats)

def test_analyze_text_empty():
    text = ""
    result = text_stats.analyze_text(text)
    assert result == {
        'line_count': 0,
        'word_count': 0,
        'character_count': 0,
        'word_frequencies': {}
    }

def test_analyze_text_single_line():
    text = "Hello, World!"
    result = text_stats.analyze_text(text)
    assert result['line_count'] == 1
    assert result['word_count'] == 2
    assert result['character_count'] == 13
    frequencies = result['word_frequencies']
    assert len(frequencies) == 2
    assert frequencies["hello"] == 1
    assert frequencies["world"] == 1

def test_analyze_text_multiple_lines():
    text = "Line 1\nLine 2\nLine 3"
    result = text_stats.analyze_text(text)
    assert result['line_count'] == 3
    assert result['word_count'] == 6
    assert result['character_count'] == 17

def test_analyze_text_word_frequencies():
    text = "apple apple banana orange orange"
    result = text_stats.analyze_text(text)
    frequencies = result['word_frequencies']
    assert len(frequencies) == 4
    assert frequencies["apple"] == 2
    assert frequencies["banana"] == 1
    assert frequencies["orange"] == 2

def test_cli_usage():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        file.write("Hello, World!")
        file.flush()
        result = subprocess.run(["python", os.environ['CANDIDATE_PATH'], file.name], capture_output=True)
        assert result.returncode == 0
        json_result = json.loads(result.stdout.decode('utf-8'))
        assert json_result['line_count'] == 1
        assert json_result['word_count'] == 2
        assert json_result['character_count'] == 13

def test_cli_invalid_usage():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        file.write("Hello, World!")
        file.flush()
        result = subprocess.run(["python", os.environ['CANDIDATE_PATH'], "invalid_file"], capture_output=True)
        assert result.returncode == 1
        error_message = result.stderr.decode('utf-8').strip()
        assert error_message.startswith("Error: ")

def test_cli_empty_file():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        file.write("")
        file.flush()
        result = subprocess.run(["python", os.environ['CANDIDATE_PATH'], file.name], capture_output=True)
        assert result.returncode == 0
        json_result = json.loads(result.stdout.decode('utf-8'))
        assert json_result == {
            'line_count': 0,
            'word_count': 0,
            'character_count': 0,
            'word_frequencies': {}
        }