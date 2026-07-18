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
        except Exception as e:
            assert str(e) == "Error reading JSON files: Expecting value"

def test_merge_json_cli():
    # Create two valid JSON files and a temporary directory for the CLI output
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2, \
         tempfile.TemporaryDirectory() as tmpdir:
        json.dump({"a": 1}, f1)
        json.dump({"b": 2}, f2)

        # Run the CLI with the two JSON files
        subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], str(f1.name), str(f2.name)],
                       capture_output=True, text=True)

        # Check that the merged JSON file was created correctly
        merged_json_path = Path(tmpdir) / 'merged.json'
        assert merged_json_path.exists()
        with open(merged_json_path, 'r') as f_out:
            merged_json = json.load(f_out)
            assert merged_json == {"a": 1, "b": 2}

if __name__ == "__main__":
    test_merge_json_valid()
    test_merge_json_invalid()
    test_merge_json_cli()