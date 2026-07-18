import os
import json
import tempfile
import pathlib
import subprocess
from io import StringIO
import importlib.util
import sys

# Load the candidate module
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    # Test valid case: count lines, words, characters and word frequencies in a sample text
    sample_text = "This is a sample text.\nIt has multiple lines."
    result = candidate_module.analyze_text(sample_text)
    assert result['lines'] == 2
    assert result['words'] == 6
    assert result['characters'] == 34
    word_freqs = result['word_frequencies']
    assert len(word_freqs) == 5
    assert word_freqs['this'] == 1
    assert word_freqs['is'] == 1
    assert word_freqs['a'] == 1
    assert word_freqs['sample'] == 1
    assert word_freqs['text.'] == 1

def test_analyze_empty_text():
    # Test invalid case: count lines, words, characters and word frequencies in an empty text
    result = candidate_module.analyze_text("")
    assert result['lines'] == 0
    assert result['words'] == 0
    assert result['characters'] == 0
    word_freqs = result['word_frequencies']
    assert len(word_freqs) == 0

def test_cli():
    # Test command-line interface: read a UTF-8 file and emit JSON
    sample_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8')
    sample_text = "This is a sample text.\nIt has multiple lines."
    sample_file.write(sample_text)
    sample_file.flush()
    try:
        # Run the candidate with the sample file as input
        process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], sample_file.name],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, error = process.communicate(input=sample_text.encode('utf-8'), timeout=1)
        assert process.returncode == 0
        result = json.loads(output.decode('utf-8'))
        assert result['lines'] == 2
        assert result['words'] == 6
        assert result['characters'] == 34
        word_freqs = result['word_frequencies']
        assert len(word_freqs) == 5
        assert word_freqs['this'] == 1
        assert word_freqs['is'] == 1
        assert word_freqs['a'] == 1
        assert word_freqs['sample'] == 1
        assert word_freqs['text.'] == 1
    finally:
        sample_file.close()

def test_invalid_input():
    # Test invalid case: count lines, words, characters and word frequencies in a non-UTF-8 file
    sample_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-16')
    sample_text = "This is a sample text.\nIt has multiple lines."
    sample_file.write(sample_text)
    sample_file.flush()
    try:
        # Run the candidate with the sample file as input
        process = subprocess.Popen([sys.executable, os.environ['CANDIDATE_PATH'], sample_file.name],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, error = process.communicate(timeout=1)
        assert process.returncode != 0
    finally:
        sample_file.close()

if __name__ == '__main__':
    test_analyze_text()
    test_analyze_empty_text()
    test_cli()
    test_invalid_input()