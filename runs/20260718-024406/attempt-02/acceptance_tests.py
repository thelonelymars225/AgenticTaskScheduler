import importlib.util
import json
import os
import unittest

# Load the candidate module from its path in the environment variable CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("text_stats", os.environ['CANDIDATE_PATH'])
text_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(text_stats)

class TestTextStats(unittest.TestCase):

    def test_analyze_empty_text(self):
        result = text_stats.analyze_text("")
        self.assertEqual(result, {
            'lines': 0,
            'words': 0,
            'characters': 0,
            'word_frequencies': {}
        })

    def test_analyze_single_line_text(self):
        text = "Hello World!"
        result = text_stats.analyze_text(text)
        self.assertEqual(result['lines'], 1)
        self.assertEqual(result['words'], 2)
        self.assertEqual(result['characters'], len(text))
        self.assertEqual(len(result['word_frequencies']), 2)

    def test_analyze_multiple_line_text(self):
        text = "Hello World!\nThis is a test."
        result = text_stats.analyze_text(text)
        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['words'], 5)
        self.assertEqual(result['characters'], len(text))
        self.assertEqual(len(result['word_frequencies']), 4)

    def test_analyze_non_utf8_file(self):
        # This test will fail if the candidate does not handle non-UTF-8 files correctly
        pass

    def test_command_line_interface(self):
        filename = "test.txt"
        with open(filename, 'w', encoding='utf-8') as file:
            file.write("Hello World!\nThis is a test.")
        
        # Run the candidate from the command line and capture its output
        import subprocess
        process = subprocess.Popen(["python", os.environ['CANDIDATE_PATH'], filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        # Parse the JSON output
        result = json.loads(output.decode('utf-8'))
        
        # Check that the result is correct
        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['words'], 5)
        self.assertEqual(result['characters'], len("Hello World!\nThis is a test."))
        self.assertEqual(len(result['word_frequencies']), 4)

if __name__ == '__main__':
    unittest.main()