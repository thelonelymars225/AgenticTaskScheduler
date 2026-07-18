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

def test_merge_valid():
    # Create two valid JSON files
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        json.dump({"b": 2}, f2)

        # Merge the JSON files
        merged_json = merge_json.merge_json(json.load(f1), json.load(f2))

        # Check that the merged JSON is correct
        assert merged_json == {"a": 1, "b": 2}

def test_merge_invalid():
    # Create two invalid JSON files (one with a missing key)
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        json.dump({"b": 2}, f2)

        # Try to merge the JSON files
        try:
            merged_json = merge_json.merge_json(json.load(f1), json.load(f2))
        except (json.JSONDecodeError, TypeError) as e:
            assert str(e) == "Expecting value: line 1 column 4 (char 5)"

def test_merge_conflicting_scalar_values():
    # Create two JSON files with conflicting scalar values
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        json.dump({"a": 1}, f1)
        json.dump({"a": 2}, f2)

        # Merge the JSON files
        merged_json = merge_json.merge_json(json.load(f1), json.load(f2))

        # Check that the merged JSON has the first object's value for conflicting scalar values
        assert merged_json == {"a": 1}

def test_cli():
    # Run the CLI with two valid JSON files
    sys.argv = ["merge_json.py", "test_data/valid.json", "test_data/valid.json"]
    sys.exit_status = merge_json.main()
    assert sys.exit_status == 0

    # Run the CLI with two invalid JSON files
    sys.argv = ["merge_json.py", "test_data/invalid.json", "test_data/invalid.json"]
    sys.exit_status = merge_json.main()
    assert sys.exit_status != 0

if __name__ == "__main__":
    test_merge_valid()
    test_merge_invalid()
    test_merge_conflicting_scalar_values()
    test_cli()