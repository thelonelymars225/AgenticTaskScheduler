import sys
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

class TestLogSummarizer(unittest.TestCase):

    def test_valid_case(self):
        # Create a valid log file
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            f.write('INFO: message 1\n')
            f.write('DEBUG: message 2\n')
            f.write('INFO: message 3\n')

            # Run the candidate on this log file
            process = subprocess.Popen([sys.executable, CANDIDATE_PATH],
                                      stdin=f.file,
                                      stdout=subprocess.PIPE)
            output, _ = process.communicate()

            # Parse the JSON output
            summary = json.loads(output.decode('utf-8'))

            # Check that we got the expected counts
            self.assertEqual(summary['INFO'], 2)
            self.assertEqual(summary['DEBUG'], 1)

    def test_invalid_case(self):
        # Create an invalid log file with no timestamp or level
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            f.write('message\n')

            # Run the candidate on this log file
            process = subprocess.Popen([sys.executable, CANDIDATE_PATH],
                                      stdin=f.file,
                                      stdout=subprocess.PIPE)
            output, _ = process.communicate()

            # Check that we got an error message
            self.assertIn('Error parsing log line: message', output.decode('utf-8'))

    def test_empty_input(self):
        # Run the candidate on an empty input file
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            process = subprocess.Popen([sys.executable, CANDIDATE_PATH],
                                      stdin=f.file,
                                      stdout=subprocess.PIPE)
            output, _ = process.communicate()

            # Check that we got an empty summary
            self.assertEqual(json.loads(output.decode('utf-8')), {})

if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]])