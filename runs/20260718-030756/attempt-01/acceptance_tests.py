import json
import os
import importlib.util
import tempfile
import shutil
import subprocess

# Load the candidate module
spec = importlib.util.spec_from_file_location("merge_json", os.environ['CANDIDATE_PATH'])
merge_json_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_json_module)

def test_merge_json():
    # Test valid case: merge two JSON objects with no conflicts
    json1 = {'a': 1, 'b': 2}
    json2 = {'c': 3, 'd': 4}
    merged = merge_json_module.merge_json(json1, json2)
    assert merged == {'a': 1, 'b': 2, 'c': 3, 'd': 4}

    # Test invalid case: merge two JSON objects with conflicting scalar values
    json1 = {'a': 1}
    json2 = {'a': 2}
    merged = merge_json_module.merge_json(json1, json2)
    assert merged == {'a': 2}  # Deterministic behavior for conflicting scalars

def test_cli():
    # Create temporary input files
    with tempfile.NamedTemporaryFile(suffix='.json') as f1, \
         tempfile.NamedTemporaryFile(suffix='.json') as f2:
        json.dump({'a': 1, 'b': 2}, f1)
        json.dump({'c': 3, 'd': 4}, f2)

        # Run the CLI
        subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name], check=True)

        # Read the merged JSON file
        with open('merged.json', 'r') as f_out:
            merged_json = json.load(f_out)
            assert merged_json == {'a': 1, 'b': 2, 'c': 3, 'd': 4}

def test_cli_invalid_input():
    # Create temporary input files
    with tempfile.NamedTemporaryFile(suffix='.json') as f1:
        json.dump({'a': 1}, f1)

        # Run the CLI with invalid number of arguments
        try:
            subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name], check=True)
            assert False, "Expected non-zero exit code"
        except subprocess.CalledProcessError as e:
            assert e.returncode != 0

if __name__ == "__main__":
    test_merge_json()
    test_cli()
    test_cli_invalid_input()