import os
import importlib.util
import json
from unittest.mock import patch, MagicMock
import tempfile
import re

# Load the candidate module from its path in the environment variable CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("text_stats", os.environ['CANDIDATE_PATH'])
text_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(text_stats)

def test_count_lines():
    text = "Hello\nWorld"
    assert text_stats.count_lines(text) == 2

def test_count_words():
    text = "Hello World, this is a test."
    assert text_stats.count_words(text) == 6

def test_count_characters():
    text = "Hello World!"
    assert text_stats.count_characters(text) == 13

def test_word_frequencies():
    text = "apple apple banana"
    frequencies = text_stats.word_frequencies(text)
    assert len(frequencies) == 3
    assert frequencies['apple'] == 2
    assert frequencies['banana'] == 1

def test_analyze_text_empty_string():
    text = ""
    result = text_stats.TextStats.analyze_text(text)
    assert result == {
        'lines': 0,
        'words': 0,
        'characters': 0,
        'word_frequencies': {}
    }

def test_analyze_text_utf8_file(tmp_path):
    filename = str(tmp_path / "test.txt")
    with open(filename, "w", encoding="utf-8") as file:
        file.write("Hello\nWorld!")
    
    # Mock sys.argv to pass the filename
    with patch.object(text_stats.sys, 'argv', [__file__, filename]):
        result = text_stats.TextStats.analyze_text(open(filename, 'r', encoding='utf-8').read())
        assert isinstance(result, dict)
        assert result['lines'] == 2
        assert result['words'] == 2
        assert result['characters'] == 13

def test_analyze_text_invalid_file():
    filename = "non_existent_file.txt"
    with patch.object(text_stats.sys, 'argv', [__file__, filename]):
        try:
            text_stats.TextStats.analyze_text(open(filename, 'r', encoding='utf-8').read())
            assert False
        except Exception as e:
            assert str(e) == "Error: [Errno 2] No such file or directory: 'non_existent_file.txt'"

def test_cli():
    # Create a temporary input file with some text
    filename = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8').name
    with open(filename, 'w') as file:
        file.write("Hello\nWorld!")
    
    # Mock sys.argv to pass the filename
    with patch.object(text_stats.sys, 'argv', [__file__, filename]):
        # Run the CLI and capture its output
        captured_output = MagicMock()
        with patch.object(text_stats.sys.stdout, 'write', captured_output):
            text_stats.TextStats.analyze_text(open(filename, 'r', encoding='utf-8').read())
        
        # Check that the output is in JSON format
        json.loads(captured_output.call_args[0][0])