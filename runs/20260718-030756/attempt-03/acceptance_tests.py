import importlib.util
import json
import os
import tempfile
import unittest

# Load the merge_json module from the candidate path
spec = importlib.util.spec_from_file_location("merge_json", os.environ['CANDIDATE_PATH'])
merge_json_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_json_module)

class TestMergeJson(unittest.TestCase):

    def test_merge_valid(self):
        # Create two valid JSON files
        with tempfile.NamedTemporaryFile(suffix='.json') as f1, \
             tempfile.NamedTemporaryFile(suffix='.json') as f2:
            json.dump({'a': 1}, f1)
            json.dump({'b': 2}, f2)

            # Merge the JSON files
            merge_json_module.main([f1.name, f2.name])

            # Load and verify the merged JSON file
            with open('merged.json', 'r') as f_out:
                merged_json = json.load(f_out)
                self.assertEqual(merged_json, {'a': 1, 'b': 2})

    def test_merge_empty(self):
        # Create two empty JSON files
        with tempfile.NamedTemporaryFile(suffix='.json') as f1, \
             tempfile.NamedTemporaryFile(suffix='.json') as f2:
            json.dump({}, f1)
            json.dump({}, f2)

            # Merge the JSON files
            merge_json_module.main([f1.name, f2.name])

            # Load and verify the merged JSON file
            with open('merged.json', 'r') as f_out:
                merged_json = json.load(f_out)
                self.assertEqual(merged_json, {})

    def test_merge_invalid(self):
        # Create two invalid JSON files (one empty, one malformed)
        with tempfile.NamedTemporaryFile(suffix='.json') as f1, \
             tempfile.NamedTemporaryFile(suffix='.json') as f2:
            json.dump({}, f1)  # Empty file
            f2.write(b'invalid json')
            f2.seek(0)

            # Attempt to merge the JSON files (should fail)
            with self.assertRaises(SystemExit):
                merge_json_module.main([f1.name, f2.name])

    def test_merge_conflicting_keys(self):
        # Create two valid JSON files with conflicting keys
        with tempfile.NamedTemporaryFile(suffix='.json') as f1, \
             tempfile.NamedTemporaryFile(suffix='.json') as f2:
            json.dump({'a': 1}, f1)
            json.dump({'a': 2}, f2)

            # Merge the JSON files
            merge_json_module.main([f1.name, f2.name])

            # Load and verify the merged JSON file
            with open('merged.json', 'r') as f_out:
                merged_json = json.load(f_out)
                self.assertEqual(merged_json, {'a': 2})

if __name__ == "__main__":
    unittest.main()