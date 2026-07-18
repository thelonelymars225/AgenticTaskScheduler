import os
import sys
import tempfile
import json
from pathlib import Path
import importlib.util
import subprocess

# Load candidate from environment variable CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    # Test valid case: analyze a sample text
    sample_text = "This is a sample text with multiple lines.\nIt has several words and characters."
    stats = candidate_module.analyze_text(sample_text)
    assert stats['lines'] == 2
    assert stats['words'] == 7
    assert stats['characters'] == 46
    word_freqs = stats['word_frequencies']
    assert len(word_freqs) == 6
    assert word_freqs['this'] == 1
    assert word_freqs['is'] == 1

def test_analyze_empty_text():
    # Test invalid case: analyze an empty text
    empty_text = ""
    stats = candidate_module.analyze_text(empty_text)
    assert stats['lines'] == 0
    assert stats['words'] == 0
    assert stats['characters'] == 0
    word_freqs = stats['word_frequencies']
    assert len(word_freqs) == 0

def test_cli():
    # Test command-line interface: analyze a file and emit JSON
    temp_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8')
    sample_text = "This is a sample text with multiple lines.\nIt has several words and characters."
    temp_file.write(sample_text)
    temp_file.flush()
    try:
        # Run the candidate as a subprocess, passing the temporary file path
        process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], temp_file.name],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, error = process.communicate(input=None, timeout=1)
        if process.returncode != 0:
            raise AssertionError(f"Error: {error.decode('utf-8')}")
        stats = json.loads(output.decode('utf-8'))
        assert stats['lines'] == 2
        assert stats['words'] == 7
        assert stats['characters'] == 46
    finally:
        temp_file.close()

if __name__ == '__main__':
    test_analyze_text()
    test_analyze_empty_text()
    test_cli()