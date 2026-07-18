import os
import sys
import tempfile
import json
from pathlib import Path
import importlib.util
import unittest

# Load candidate from file
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

class TestTextStatistics(unittest.TestCase):

    def test_valid_case(self):
        # Create a temporary text file with some content
        temp_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8')
        temp_file.write("This is a sample text.\n")
        temp_file.write("It has multiple lines.")
        temp_file.flush()

        # Run the candidate on this file
        sys.argv = [sys.argv[0], temp_file.name]
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['CANDIDATE_PATH'] = Path(tmpdir) / 'candidate.py'
            import candidate_module  # noqa: F401
            try:
                result = candidate_module.analyze_text(temp_file.read())
                self.assertEqual(result, {
                    'lines': 2,
                    'words': 6,
                    'characters': 34,
                    'word_frequencies': {'this': 1, 'is': 1, 'a': 1, 'sample': 1, 'text': 1, 'it': 1, 'has': 1, 'multiple': 1, 'lines': 1}
                })
            except Exception as e:
                self.fail(f"Unexpected exception: {e}")

    def test_invalid_case(self):
        # Create a temporary text file with no content
        temp_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8')
        temp_file.write("")
        temp_file.flush()

        # Run the candidate on this file
        sys.argv = [sys.argv[0], temp_file.name]
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['CANDIDATE_PATH'] = Path(tmpdir) / 'candidate.py'
            import candidate_module  # noqa: F401
            try:
                result = candidate_module.analyze_text(temp_file.read())
                self.assertEqual(result, {
                    'lines': 1,
                    'words': 0,
                    'characters': 2,
                    'word_frequencies': {}
                })
            except Exception as e:
                self.fail(f"Unexpected exception: {e}")

if __name__ == '__main__':
    unittest.main(argv=sys.argv)