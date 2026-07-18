import sys
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

# Load candidate from file
spec = importlib.util.spec_from_file_location("merge_json", os.environ['CANDIDATE_PATH'])
merge_json = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_json)

class TestMergeJson(unittest.TestCase):

    def test_valid_merge(self):
        # Create two valid JSON files
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f1, \
             tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f2:
            json.dump({'a': 1}, f1)
            json.dump({'b': 2}, f2)

            # Merge the two files
            subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name],
                           check=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           stdin=subprocess.DEVNULL)

            # Read the merged JSON file
            with open('merged.json', 'r') as f_out:
                merged_json = json.load(f_out)
                self.assertEqual(merged_json, {'a': 1, 'b': 2})

    def test_invalid_merge(self):
        # Create two invalid JSON files (one empty and one malformed)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f1, \
             tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f2:
            json.dump({}, f1)  # Empty file
            f2.write('malformed json\n')
            f2.flush()

            # Attempt to merge the two files
            with self.assertRaises(SystemExit):
                subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name],
                               check=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL)

if __name__ == "__main__":
    unittest.main(argv=[os.environ['CANDIDATE_PATH']])