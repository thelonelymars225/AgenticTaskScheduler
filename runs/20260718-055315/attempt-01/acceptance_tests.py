import os
import sys
import tempfile
import pathlib
from io import StringIO
import importlib.util
import json

# Load candidate from file
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_analyze_text():
    # Test valid case: analyze a sample text
    sample_text = "This is a sample text.\nIt has multiple lines."
    stats = candidate_module.analyze_text(sample_text)
    assert stats['lines'] == 2
    assert stats['words'] == 6
    assert stats['characters'] == 34
    word_freqs = stats['word_frequencies']
    assert len(word_freqs) == 5
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
    sample_text = "This is a sample text.\nIt has multiple lines."
    temp_file.write(sample_text)
    temp_file.flush()
    sys.argv = ['text_stats.py', temp_file.name]
    candidate_module.main()
    output = StringIO(sys.stdout.getvalue())
    stats = json.loads(output.getvalue())
    assert stats['lines'] == 2
    assert stats['words'] == 6
    assert stats['characters'] == 34
    word_freqs = stats['word_frequencies']
    assert len(word_freqs) == 5
    assert word_freqs['this'] == 1
    assert word_freqs['is'] == 1

def test_cli_invalid_file():
    # Test command-line interface: analyze a non-existent file
    sys.argv = ['text_stats.py', 'non_existent_file.txt']
    candidate_module.main()
    output = StringIO(sys.stderr.getvalue())
    error_message = output.getvalue().strip()
    assert "Error:" in error_message

if __name__ == '__main__':
    test_analyze_text()
    test_analyze_empty_text()
    test_cli()
    test_cli_invalid_file()