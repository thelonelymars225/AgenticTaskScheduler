import json
import os
import sys
from pathlib import Path
import importlib.util
import tempfile
import subprocess

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
        f2.write("{")
        f2.flush()

        # Try to merge the two JSON files
        try:
            merged_json = merge_json.merge_json(json.load(f1), json.load(f2))
            assert False, "Expected JSONDecodeError"
        except json.JSONDecodeError:
            pass

def test_merge_json_cli():
    # Create a valid and an invalid input file for the CLI
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        json.dump({"b": 2}, f2)

        # Run the CLI with valid input
        subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name], check=True)

        # Check that the merged JSON file was created correctly
        with open('merged.json', 'r') as f_out:
            assert json.load(f_out) == {"a": 1, "b": 2}

        # Run the CLI with invalid input
        subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name], check=True)

if __name__ == "__main__":
    test_merge_json_valid()
    test_merge_json_invalid()
    test_merge_json_cli()