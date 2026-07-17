import os
import importlib.util
import json
from unittest.mock import patch, MagicMock

# Load the candidate module from its path in the environment variable
spec = importlib.util.spec_from_file_location("text_stats", os.environ['CANDIDATE_PATH'])
text_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(text_stats)

def test_analyze_text_empty():
    result = text_stats.analyze_text("")
    assert result == {
        'lines': 0,
        'words': 0,
        'characters': 0,
        'word_frequencies': {}
    }

def test_analyze_text_single_line():
    text = "Hello, World!"
    result = text_stats.analyze_text(text)
    assert result['lines'] == 1
    assert result['words'] == 2
    assert result['characters'] == len(text)
    frequencies = result['word_frequencies']
    assert len(frequencies) == 2
    assert frequencies["hello"] == 1
    assert frequencies["world"] == 1

def test_analyze_text_multiple_lines():
    text = "Line 1\nLine 2\nLine 3"
    result = text_stats.analyze_text(text)
    assert result['lines'] == 3
    assert result['words'] == 6
    assert result['characters'] == len(text)

def test_command_line_interface_valid_file():
    with patch('sys.argv', ["text_stats.py", "test.txt"]):
        with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
            with open("test.txt", 'w') as file:
                file.write("Hello, World!")
            text_stats.main()
            result = json.loads(mock_stdout.getvalue())
            assert result == {
                'lines': 1,
                'words': 2,
                'characters': len("Hello, World!"),
                'word_frequencies': {"hello": 1, "world": 1}
            }

def test_command_line_interface_invalid_file():
    with patch('sys.argv', ["text_stats.py", "non_existent.txt"]):
        with patch('sys.stderr', new_callable=MagicMock) as mock_stderr:
            text_stats.main()
            assert mock_stderr.getvalue().startswith("Error: ")

def test_command_line_interface_empty_file():
    with patch('sys.argv', ["text_stats.py", "test.txt"]):
        with open("test.txt", 'w') as file:
            file.write("")
        with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
            text_stats.main()
            result = json.loads(mock_stdout.getvalue())
            assert result == {
                'lines': 0,
                'words': 0,
                'characters': 0,
                'word_frequencies': {}
            }