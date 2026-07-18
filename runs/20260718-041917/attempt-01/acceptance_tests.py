import os
import sys
import tempfile
import json
from pathlib import Path
import importlib.util
import unittest

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

class TestTextStatistics(unittest.TestCase):

    def test_analyze_text(self):
        text = "Hello, World!\nThis is a test."
        result = candidate_module.analyze_text(text)
        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['words'], 5)
        self.assertEqual(result['characters'], 24)
        frequencies = result['word_frequencies']
        self.assertIn('hello', frequencies)
        self.assertIn('world', frequencies)
        self.assertIn('this', frequencies)
        self.assertIn('is', frequencies)
        self.assertIn('a', frequencies)
        self.assertIn('test', frequencies)

    def test_empty_text(self):
        text = ""
        result = candidate_module.analyze_text(text)
        self.assertEqual(result['lines'], 0)
        self.assertEqual(result['words'], 0)
        self.assertEqual(result['characters'], 0)
        self.assertEqual(result['word_frequencies'], {})

    def test_invalid_file_path(self):
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
            file.write("Hello, World!")
            file.flush()
            sys.argv = ['python', CANDIDATE_PATH, 'invalid_path']
            try:
                candidate_module.main()
                self.fail("Expected exception not raised")
            except SystemExit:
                pass

    def test_invalid_file_contents(self):
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as file:
            file.write("Invalid UTF-8 sequence")
            file.flush()
            sys.argv = ['python', CANDIDATE_PATH, str(file.name)]
            try:
                candidate_module.main()
                self.fail("Expected exception not raised")
            except UnicodeDecodeError:
                pass

if __name__ == '__main__':
    unittest.main(argv=sys.argv)