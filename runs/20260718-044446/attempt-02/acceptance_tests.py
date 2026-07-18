import importlib.util
import json
import os
import tempfile
import unittest

# Load the candidate module from its path in the environment variable CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

class TestTextStatistics(unittest.TestCase):

    def test_analyze_text(self):
        # Create a sample text with some lines, words and characters
        text = """This is a sample text.
It has multiple lines.
Each line contains several words."""

        result = candidate_module.analyze_text(text)
        self.assertEqual(result['line_count'], 3)
        self.assertEqual(result['word_count'], 13)
        self.assertEqual(result['character_count'], 64)

        # Test word frequencies
        expected_frequencies = {'this': 1, 'is': 1, 'a': 1, 'sample': 1, 'text': 1,
                                'it': 1, 'has': 1, 'multiple': 1, 'lines': 1,
                                'each': 1, 'line': 2, 'contains': 1, 'several': 1, 'words': 1}
        self.assertEqual(result['word_frequencies'], expected_frequencies)

    def test_empty_text(self):
        # Test analyzing an empty text
        result = candidate_module.analyze_text('')
        self.assertEqual(result['line_count'], 0)
        self.assertEqual(result['word_count'], 0)
        self.assertEqual(result['character_count'], 0)
        self.assertEqual(result['word_frequencies'], {})

    def test_invalid_file_path(self):
        # Test analyzing a non-existent file
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            f.write('Invalid file path')
            f.flush()
            args = ['--file', 'non_existent_file.txt']
            with self.assertRaises(SystemExit) as e:
                candidate_module.main(args)
            self.assertEqual(e.exception.code, 1)

    def test_invalid_utf8(self):
        # Test analyzing a file with invalid UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w+b') as f:
            f.write(b'Invalid \xff\xfe text')
            f.flush()
            args = ['--file', f.name]
            with self.assertRaises(SystemExit) as e:
                candidate_module.main(args)
            self.assertEqual(e.exception.code, 1)

if __name__ == '__main__':
    unittest.main(argv=['-v'])