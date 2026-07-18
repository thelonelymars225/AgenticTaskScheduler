import os
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
import sys

# Load candidate module from environment variable CANDIDATE_PATH
candidate_path = os.environ['CANDIDATE_PATH']
spec = importlib.util.spec_from_file_location('analyze_text', candidate_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestAnalyzeText(unittest.TestCase):

    def test_tokenize(self):
        text = "Hello, world! This is a test."
        tokens = module.tokenize(text)
        self.assertEqual(tokens, ['hello', 'world', 'this', 'is', 'a', 'test'])

    def test_frequency_mapping(self):
        text = "This is a test. This is only a test."
        freq_map = module.frequency_mapping(text)
        self.assertEqual(freq_map, {'this': 2, 'is': 2, 'a': 2, 'test': 2})

    def test_line_count(self):
        text = "Line 1\nLine 2\n\nLine 4"
        self.assertEqual(module.line_count(text), 3)

    def test_character_count(self):
        text = "Hello, world!"
        self.assertEqual(module.character_count(text), 13)

    def test_analyze_text(self):
        text = "This is a test. This is only a test."
        result = module.analyze_text(text)
        self.assertEqual(result['words'], 6)
        self.assertEqual(result['frequency'], {'this': 2, 'is': 2, 'a': 2, 'test': 2})
        self.assertEqual(result['lines'], 1)
        self.assertEqual(result['characters'], 26)

    def test_analyze_file(self):
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
            text = "This is a test. This is only a test."
            tmp.write(text)
            tmp.flush()
            result = module.analyze_file(tmp.name)
            self.assertEqual(result['words'], 6)
            self.assertEqual(result['frequency'], {'this': 2, 'is': 2, 'a': 2, 'test': 2})
            self.assertEqual(result['lines'], 1)
            self.assertEqual(result['characters'], 26)

    def test_main_cli(self):
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
            text = "This is a test. This is only a test."
            tmp.write(text)
            tmp.flush()
            result = subprocess.run([sys.executable, candidate_path, tmp.name], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            json_result = json.loads(result.stdout)
            self.assertEqual(json_result['words'], 6)
            self.assertEqual(json_result['frequency'], {'this': 2, 'is': 2, 'a': 2, 'test': 2})
            self.assertEqual(json_result['lines'], 1)
            self.assertEqual(json_result['characters'], 26)

if __name__ == "__main__":
    unittest.main()