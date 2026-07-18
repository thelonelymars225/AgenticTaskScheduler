import os
import sys
from pathlib import Path
import tempfile
import json
import importlib.util
import argparse

# Load candidate from file
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    # Test valid case: analyze a sample text
    sample_text = "This is a sample text with multiple lines.\nIt has several words and characters."
    result = candidate_module.analyze_text(sample_text)
    assert isinstance(result, dict), f"Expected dictionary, got {type(result)}"
    assert 'lines' in result, f"Missing key 'lines'"
    assert 'words' in result, f"Missing key 'words'"
    assert 'characters' in result, f"Missing key 'characters'"
    assert 'word_frequencies' in result, f"Missing key 'word_frequencies'"

def test_analyze_text_empty():
    # Test invalid case: analyze an empty text
    sample_text = ""
    result = candidate_module.analyze_text(sample_text)
    assert isinstance(result, dict), f"Expected dictionary, got {type(result)}"
    assert 'lines' in result, f"Missing key 'lines'"
    assert 'words' in result, f"Missing key 'words'"
    assert 'characters' in result, f"Missing key 'characters'"
    assert 'word_frequencies' in result, f"Missing key 'word_frequencies'"
    assert result['lines'] == 0
    assert result['words'] == 0
    assert result['characters'] == 0

def test_cli():
    # Test command-line interface: analyze a sample file
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        sample_text = "This is a sample text with multiple lines.\nIt has several words and characters."
        f.write(sample_text)
        f.flush()
        sys.argv = ['main.py', f.name]
        candidate_module.main()

if __name__ == '__main__':
    test_analyze_text()
    test_analyze_text_empty()
    test_cli()