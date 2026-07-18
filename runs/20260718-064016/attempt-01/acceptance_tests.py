import json
import os
import sys
import importlib.util
from pathlib import Path
import tempfile
import subprocess

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    text = "This is a sample text."
    result = candidate_module.analyze_text(text)
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'characters' in result
    assert 'words' in result
    assert 'frequency' in result

def test_analyze_file():
    file_path = Path(__file__).parent / "test.txt"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("This is a sample text.")
    
    result = candidate_module.analyze_file(str(file_path))
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'characters' in result
    assert 'words' in result
    assert 'frequency' in result

def test_invalid_input():
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        f.write("This is a sample text.")
        f.flush()
        f.seek(0)
        
        # Test invalid input type (None)
        try:
            candidate_module.analyze_text(None)
            assert False, "Expected TypeError"
        except TypeError:
            pass
        
        # Test invalid input type (int)
        try:
            candidate_module.analyze_text(123)
            assert False, "Expected TypeError"
        except TypeError:
            pass

def test_cli():
    file_path = Path(__file__).parent / "test.txt"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("This is a sample text.")
    
    # Test valid case
    process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], str(file_path)], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    result = json.loads(output.decode('utf-8'))
    assert isinstance(result, dict)
    assert 'lines' in result
    assert 'characters' in result
    assert 'words' in result
    assert 'frequency' in result
    
    # Test invalid case (non-existent file)
    process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], str(file_path)], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    error_message = json.loads(output.decode('utf-8'))['error']
    assert "Error: FileNotFoundError" in error_message

if __name__ == "__main__":
    test_analyze_text()
    test_analyze_file()
    test_invalid_input()
    test_cli()