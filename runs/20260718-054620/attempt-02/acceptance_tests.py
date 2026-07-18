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

        # Merge the JSON files
        merged_json = merge_json.merge_json(json.load(f1), json.load(f2))

        # Check that the merged JSON is correct
        assert merged_json == {"a": 1, "b": 2}

def test_merge_json_invalid():
    # Create two invalid JSON files (one with a missing key)
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        json.dump({"b": 2}, f2)

        # Try to merge the JSON files
        try:
            merged_json = merge_json.merge_json(json.load(f1), json.load(f2))
            assert False, "Expected a ValueError"
        except ValueError as e:
            assert str(e) == "Conflicting keys: 'b'"

def test_merge_json_cli():
    # Create two valid JSON files
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        json.dump({"b": 2}, f2)

        # Run the CLI
        with open(f1.name, 'r') as f_in1, open(f2.name, 'r') as f_in2, \
             tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f_out:
            subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f_in1.name, f_in2.name], 
                          stdin=subprocess.PIPE, stdout=f_out)

        # Check that the merged JSON is correct
        with open(f_out.name, 'r') as f_out:
            assert json.load(f_out) == {"a": 1, "b": 2}

if __name__ == "__main__":
    test_merge_json_valid()
    test_merge_json_invalid()
    test_merge_json_cli()