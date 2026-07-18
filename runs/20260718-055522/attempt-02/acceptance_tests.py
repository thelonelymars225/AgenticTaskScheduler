import sys
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("merge_json", os.environ['CANDIDATE_PATH'])
merge_json = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_json)

class TestMergeJson(unittest.TestCase):

    def test_valid_merge(self):
        # Create two valid JSON files
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
             tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
            json.dump({"a": 1}, f1)
            json.dump({"b": 2}, f2)

            # Merge the two files
            merged_json = merge_json.merge_json(json.load(f1), json.load(f2))

            # Check that the merged JSON is correct
            self.assertEqual(merged_json, {"a": 1, "b": 2})

    def test_invalid_merge(self):
        # Create two invalid JSON files (one with a missing key)
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
             tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
            json.dump({"a": 1}, f1)
            json.dump({"b": 2}, f2)

            # Try to merge the two files
            with self.assertRaises(json.JSONDecodeError):
                merge_json.merge_json(json.load(f1), json.load(f2))

    def test_cli(self):
        # Create two valid JSON files
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
             tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
            json.dump({"a": 1}, f1)
            json.dump({"b": 2}, f2)

            # Run the CLI
            subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name], check=True)

            # Check that the merged JSON file was created correctly
            with open('merged.json', 'r') as f_out:
                self.assertEqual(json.load(f_out), {"a": 1, "b": 2})

if __name__ == "__main__":
    unittest.main()