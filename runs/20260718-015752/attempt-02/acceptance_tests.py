import os
import json
import tempfile
import shutil
from io import StringIO
import importlib.util
import unittest

# Load the candidate module
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

class TestTextStatistics(unittest.TestCase):

    def test_analyze_text_empty(self):
        result = candidate_module.analyze_text("")
        self.assertEqual(result, {
            'lines': 0,
            'words': 0,
            'characters': 0,
            'word_frequencies': {}
        })

    def test_analyze_text_single_line(self):
        text = "Hello World!"
        result = candidate_module.analyze_text(text)
        self.assertEqual(result['lines'], 1)
        self.assertEqual(result['words'], 2)
        self.assertEqual(result['characters'], len(text))
        self.assertEqual(len(result['word_frequencies']), 2)

    def test_analyze_text_multiple_lines(self):
        text = "Hello World!\nThis is a test."
        result = candidate_module.analyze_text(text)
        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['words'], 5)
        self.assertEqual(result['characters'], len(text))
        self.assertEqual(len(result['word_frequencies']), 4)

    def test_analyze_text_word_frequency(self):
        text = "Hello World! Hello Again!"
        result = candidate_module.analyze_text(text)
        self.assertIn('Hello', result['word_frequencies'])
        self.assertIn('World!', result['word_frequencies'])
        self.assertEqual(result['word_frequencies']['Hello'], 2)

    def test_analyze_text_invalid_file(self):
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"Invalid UTF-8 data")
            tmp.seek(0)
            try:
                candidate_module.analyze_text(tmp.read().decode('utf-8'))
                self.fail("Expected exception not raised")
            except UnicodeDecodeError:
                pass

    def test_command_line_interface(self):
        with tempfile.NamedTemporaryFile() as tmp:
            text = "Hello World!\nThis is a test."
            tmp.write(text.encode('utf-8'))
            tmp.seek(0)
            captured_output = StringIO()
            sys.stdout = captured_output
            candidate_module.main(["--filename", tmp.name])
            sys.stdout = sys.__stdout__
            result = json.loads(captured_output.getvalue())
            self.assertEqual(result['lines'], 2)
            self.assertEqual(result['words'], 5)
            self.assertEqual(result['characters'], len(text))
            self.assertEqual(len(result['word_frequencies']), 4)

if __name__ == '__main__':
    unittest.main(argv=[os.environ['CANDIDATE_PATH']])