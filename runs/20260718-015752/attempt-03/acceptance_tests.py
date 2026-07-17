import os
import importlib.util
import json
from io import StringIO
import unittest

# Load the candidate module from its path in the environment variable CANDIDATE_PATH
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

    def test_analyze_text_punctuation(self):
        text = "Hello, World! This is a test."
        result = candidate_module.analyze_text(text)
        self.assertEqual(result['lines'], 1)
        self.assertEqual(result['words'], 5)
        self.assertEqual(result['characters'], len(text))
        self.assertEqual(len(result['word_frequencies']), 4)

    def test_analyze_text_non_utf8(self):
        text = "Hello World!".encode('latin-1')
        with self.assertRaises(UnicodeDecodeError):
            candidate_module.analyze_text(text.decode('utf-8'))

    def test_command_line_interface_valid_file(self):
        # Create a temporary file
        temp_file_path = 'temp.txt'
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write("Hello World!\nThis is a test.")

        # Run the command-line interface
        import sys
        import subprocess
        capturedOutput = StringIO()
        sys.stdout = capturedOutput
        try:
            subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], temp_file_path], check=True)
        finally:
            sys.stdout = sys.__stdout__

        # Parse the output JSON
        result = json.loads(capturedOutput.getvalue())

        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['words'], 5)
        self.assertEqual(result['characters'], len("Hello World!\nThis is a test."))
        self.assertEqual(len(result['word_frequencies']), 4)

    def test_command_line_interface_invalid_file(self):
        # Create a temporary file
        temp_file_path = 'temp.txt'
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write("Hello World!\nThis is a test.")

        # Make the file not readable
        os.chmod(temp_file_path, 0o444)

        # Run the command-line interface
        import sys
        import subprocess
        capturedOutput = StringIO()
        sys.stdout = capturedOutput
        try:
            subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], temp_file_path], check=True)
        except subprocess.CalledProcessError as e:
            self.assertEqual(e.returncode, 1)
        finally:
            sys.stdout = sys.__stdout__

    def test_command_line_interface_non_utf8_file(self):
        # Create a temporary file
        temp_file_path = 'temp.txt'
        with open(temp_file_path, 'w', encoding='latin-1') as f:
            f.write("Hello World!")

        # Run the command-line interface
        import sys
        import subprocess
        capturedOutput = StringIO()
        sys.stdout = capturedOutput
        try:
            subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], temp_file_path], check=True)
        except subprocess.CalledProcessError as e:
            self.assertEqual(e.returncode, 1)
        finally:
            sys.stdout = sys.__stdout__

if __name__ == '__main__':
    unittest.main()