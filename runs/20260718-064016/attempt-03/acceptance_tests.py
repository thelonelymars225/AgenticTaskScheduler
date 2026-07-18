import importlib.util
import os
import json
import tempfile
import re
from collections import Counter

# Load the candidate module
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    text = "This is a sample text with multiple lines."
    result = candidate_module.analyze_text(text)
    assert result["lines"] == 2
    assert result["characters"] == len(text)
    assert result["words"] == 6
    frequency = result["frequency"]
    assert set(frequency.keys()) == {"this", "is", "a", "sample", "text", "with", "multiple", "lines"}
    assert sum(frequency.values()) == 8

def test_analyze_text_empty():
    text = ""
    result = candidate_module.analyze_text(text)
    assert result["lines"] == 0
    assert result["characters"] == 0
    assert result["words"] == 0
    frequency = result["frequency"]
    assert set(frequency.keys()) == set()
    assert sum(frequency.values()) == 0

def test_analyze_text_whitespace():
    text = "   \t\n"
    result = candidate_module.analyze_text(text)
    assert result["lines"] == 1
    assert result["characters"] == len(text)
    assert result["words"] == 0
    frequency = result["frequency"]
    assert set(frequency.keys()) == set()
    assert sum(frequency.values()) == 0

def test_analyze_file():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "This is a sample text with multiple lines."
        file.write(text)
        file.flush()
        result = candidate_module.analyze_file(file.name)
        assert result["lines"] == 2
        assert result["characters"] == len(text)
        assert result["words"] == 6
        frequency = result["frequency"]
        assert set(frequency.keys()) == {"this", "is", "a", "sample", "text", "with", "multiple", "lines"}
        assert sum(frequency.values()) == 8

def test_analyze_file_empty():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = ""
        file.write(text)
        file.flush()
        result = candidate_module.analyze_file(file.name)
        assert result["lines"] == 0
        assert result["characters"] == 0
        assert result["words"] == 0
        frequency = result["frequency"]
        assert set(frequency.keys()) == set()
        assert sum(frequency.values()) == 0

def test_analyze_file_invalid_path():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "This is a sample text with multiple lines."
        file.write(text)
        file.flush()
        invalid_path = "/invalid/path"
        try:
            candidate_module.analyze_file(invalid_path)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass

def test_cli():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
        text = "This is a sample text with multiple lines."
        file.write(text)
        file.flush()
        command = f"python {os.environ['CANDIDATE_PATH']} {file.name}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        assert process.returncode == 0
        result = json.loads(output.decode('utf-8'))
        assert result["lines"] == 2
        assert result["characters"] == len(text)
        assert result["words"] == 6
        frequency = result["frequency"]
        assert set(frequency.keys()) == {"this", "is", "a", "sample", "text", "with", "multiple", "lines"}
        assert sum(frequency.values()) == 8

if __name__ == "__main__":
    test_analyze_text()
    test_analyze_text_empty()
    test_analyze_text_whitespace()
    test_analyze_file()
    test_analyze_file_empty()
    test_analyze_file_invalid_path()
    test_cli()