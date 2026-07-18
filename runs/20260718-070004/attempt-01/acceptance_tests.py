import os
import sys
from pathlib import Path
import importlib.util
import tempfile
import json
import re
from collections import Counter

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_tokenize():
    text = "Hello, world! This is a test."
    tokens = candidate_module.tokenize(text)
    assert len(tokens) == 6
    assert set(tokens) == {"hello", "world", "this", "is", "a", "test"}

def test_frequency_mapping():
    text = "This is a test. This is only a test."
    freq_map = candidate_module.frequency_mapping(text)
    assert len(freq_map) == 4
    assert list(freq_map.keys()) == ["hello", "world", "this", "is"]
    assert list(freq_map.values()) == [1, 1, 2, 2]

def test_line_count():
    text = ""
    assert candidate_module.line_count(text) == 0

    text = "Hello,\nWorld!"
    assert candidate_module.line_count(text) == 2

def test_character_count():
    text = "Hello, world!"
    assert candidate_module.character_count(text) == 13

def test_analyze_text():
    text = "This is a test. This is only a test."
    result = candidate_module.analyze_text(text)
    assert result["words"] == 6
    assert result["frequency"] == {"hello": 1, "world": 1, "this": 2, "is": 2}
    assert result["lines"] == 2
    assert result["characters"] == 13

def test_analyze_file(tmp_path):
    text = "This is a test. This is only a test."
    file_path = tmp_path / "test.txt"
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)

    result = candidate_module.analyze_file(str(file_path))
    assert result["words"] == 6
    assert result["frequency"] == {"hello": 1, "world": 1, "this": 2, "is": 2}
    assert result["lines"] == 2
    assert result["characters"] == 13

def test_cli(tmp_path):
    text = "This is a test. This is only a test."
    file_path = tmp_path / "test.txt"
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)

    # Run CLI
    import subprocess
    process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], str(file_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    # Check JSON output
    result = json.loads(output.decode('utf-8'))
    assert result["words"] == 6
    assert result["frequency"] == {"hello": 1, "world": 1, "this": 2, "is": 2}
    assert result["lines"] == 2
    assert result["characters"] == 13

    # Check error handling
    process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], str(file_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate(b"Invalid input")
    assert b"Error: Invalid input" in error

if __name__ == "__main__":
    test_tokenize()
    test_frequency_mapping()
    test_line_count()
    test_character_count()
    test_analyze_text()
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        file.write("This is a test.")
        file.flush()
        file.seek(0)
        test_analyze_file(file.name)

    # Run CLI
    import subprocess
    process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], str(tmp_path / "test.txt")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    # Check JSON output
    result = json.loads(output.decode('utf-8'))
    assert result["words"] == 6
    assert result["frequency"] == {"hello": 1, "world": 1, "this": 2, "is": 2}
    assert result["lines"] == 2
    assert result["characters"] == 13

    # Check error handling
    process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], str(tmp_path / "test.txt")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate(b"Invalid input")
    assert b"Error: Invalid input" in error