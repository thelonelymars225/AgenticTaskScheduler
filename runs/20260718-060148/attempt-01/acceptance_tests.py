import os
import sys
from pathlib import Path
import tempfile
import importlib.util
import json

# Load candidate from file
CANDIDATE_PATH = os.environ['CANDIDATE_PATH']
spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    # Test valid case: count lines, words, characters and word frequencies
    text = "Hello World!\nThis is a test.\n"
    result = candidate_module.analyze_text(text)
    assert result['lines'] == 3
    assert result['words'] == 6
    assert result['characters'] == 24
    assert result['word_frequencies'] == {'hello': 1, 'world': 1, 'this': 1, 'is': 1, 'a': 1, 'test': 1}

def test_analyze_text_empty():
    # Test invalid case: empty text
    text = ""
    result = candidate_module.analyze_text(text)
    assert result['lines'] == 0
    assert result['words'] == 0
    assert result['characters'] == 0
    assert result['word_frequencies'] == {}

def test_cli():
    # Test command-line interface: read a UTF-8 file and emit JSON
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        text = "Hello World!\nThis is a test.\n"
        f.write(text)
        f.flush()
        sys.argv = ['python', CANDIDATE_PATH, f.name]
        candidate_module.main()
        result = json.loads(f.read())
        assert result['lines'] == 3
        assert result['words'] == 6
        assert result['characters'] == 24
        assert result['word_frequencies'] == {'hello': 1, 'world': 1, 'this': 1, 'is': 1, 'a': 1, 'test': 1}

if __name__ == '__main__':
    test_analyze_text()
    test_analyze_text_empty()
    try:
        test_cli()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        exit(1)