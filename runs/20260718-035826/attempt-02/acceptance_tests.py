import importlib.util
import json
import os
import pathlib
import subprocess
import sys

# Load candidate module from file
spec = importlib.util.spec_from_file_location("merge_json", os.environ['CANDIDATE_PATH'])
merge_json_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_json_module)

def test_merge_json():
    # Test valid case: merge two JSON objects with no conflicts
    json1 = {'a': 1, 'b': 2}
    json2 = {'c': 3, 'd': 4}
    merged_json = merge_json_module.merge_json(json1, json2)
    assert merged_json == {'a': 1, 'b': 2, 'c': 3, 'd': 4}

    # Test invalid case: merge two JSON objects with conflicting scalar values
    json1 = {'a': 1}
    json2 = {'a': 2}
    merged_json = merge_json_module.merge_json(json1, json2)
    assert merged_json == {'a': 2}  # Deterministic behavior for conflicting scalar values

def test_cli():
    # Create temporary input files
    file1_path = pathlib.Path('file1.json')
    file2_path = pathlib.Path('file2.json')

    with open(file1_path, 'w') as f:
        json.dump({'a': 1}, f)
    with open(file2_path, 'w') as f:
        json.dump({'b': 2}, f)

    # Run the CLI
    subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], file1_path.as_posix(), file2_path.as_posix()], check=True)

    # Verify merged JSON output
    with open('merged.json', 'r') as f:
        merged_json = json.load(f)
        assert merged_json == {'a': 1, 'b': 2}

if __name__ == "__main__":
    test_merge_json()
    test_cli()