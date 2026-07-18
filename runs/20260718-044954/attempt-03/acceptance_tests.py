import os
import sys
from pathlib import Path
import tempfile
import importlib.util
import json

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("merge_json", os.environ['CANDIDATE_PATH'])
merge_json = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_json)

def test_merge_json_valid():
    # Create two valid JSON files
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        json.dump({"b": 2}, f2)

        # Merge the two JSON files
        merged_json = merge_json.merge_json(json.load(f1), json.load(f2))

        # Check that the merged JSON is correct
        assert merged_json == {"a": 1, "b": 2}

def test_merge_json_invalid():
    # Create a valid and an invalid JSON file
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        f2.write("Invalid JSON")
        f2.seek(0)

        # Try to merge the two JSON files
        try:
            merge_json.merge_json(json.load(f1), json.load(f2))
            assert False, "Expected JSONDecodeError"
        except json.JSONDecodeError:
            pass

def test_merge_json_cli():
    # Create a valid and an invalid input file for the CLI
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        json.dump({"b": 2}, f2)

        # Run the CLI with the two input files
        sys.argv = ["merge_json.py", f1.name, f2.name]
        try:
            merge_json.main()
        except SystemExit as e:
            assert e.code == 0

        # Check that the merged JSON file was created correctly
        with open('merged.json', 'r') as f_out:
            merged_json = json.load(f_out)
            assert merged_json == {"a": 1, "b": 2}

if __name__ == "__main__":
    test_merge_json_valid()
    test_merge_json_invalid()
    test_merge_json_cli()