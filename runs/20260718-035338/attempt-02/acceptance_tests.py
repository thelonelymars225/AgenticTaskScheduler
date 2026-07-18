import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import sys

# Load the candidate module
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text_empty_string():
    result = candidate_module.analyze_text("")
    assert result == {
        'lines': 0,
        'words': 0,
        'characters': 0,
        'word_frequencies': {}
    }

def test_analyze_text_single_line():
    text = "Hello, World!"
    result = candidate_module.analyze_text(text)
    assert result['lines'] == 1
    assert result['words'] == 2
    assert result['characters'] == len(text)
    assert result['word_frequencies'] == {'hello': 1, 'world': 1}

def test_analyze_text_multiple_lines():
    text = "Line 1\nLine 2\nLine 3"
    result = candidate_module.analyze_text(text)
    assert result['lines'] == 3
    assert result['words'] == 6
    assert result['characters'] == len(text)

def test_analyze_text_non_string_input():
    text = b"Hello, World!"
    try:
        candidate_module.analyze_text(text)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert str(e) == "Input must be a string"

def test_cli_valid_file():
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as file:
        text = "Hello, World!\nThis is a test."
        file.write(text)
        file.flush()
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], file.name], capture_output=True, text=True)
        json_result = json.loads(result.stdout)
        assert json_result == {
            'lines': 2,
            'words': 6,
            'characters': len(text),
            'word_frequencies': {'hello': 1, 'world': 1, 'this': 1, 'is': 1, 'a': 1, 'test': 1}
        }

def test_cli_invalid_file():
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as file:
        text = "Hello, World!"
        file.write(text)
        file.flush()
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], file.name], capture_output=True, text=True)
        assert "Error: File" in result.stderr

def test_cli_invalid_encoding():
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as file:
        text = b"\xff\xfeHello, World!"
        file.write(text.decode('latin1'))
        file.flush()
        result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], file.name], capture_output=True, text=True)
        assert "Error: Unable to decode" in result.stderr

if __name__ == '__main__':
    test_analyze_text_empty_string()
    test_analyze_text_single_line()
    test_analyze_text_multiple_lines()
    test_analyze_text_non_string_input()
    test_cli_valid_file()
    test_cli_invalid_file()
    test_cli_invalid_encoding()