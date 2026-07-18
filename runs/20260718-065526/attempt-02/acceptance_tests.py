import os
import sys
from pathlib import Path
import importlib.util
import json
import tempfile
import subprocess

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_merge_json():
    # Test valid case: merge two JSON objects with no conflicts
    left_data = {'a': 1, 'b': 2}
    right_data = {'c': 3, 'd': 4}
    output_path = Path(tempfile.mkstemp()[1])
    candidate_module.merge(left_data, right_data)
    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        merged_data = json.load(f)
    assert merged_data == {'a': 1, 'b': 2, 'c': 3, 'd': 4}

def test_merge_json_invalid():
    # Test invalid case: merge two JSON objects with conflicting keys
    left_data = {'a': 1}
    right_data = {'a': 2}
    output_path = Path(tempfile.mkstemp()[1])
    try:
        candidate_module.merge(left_data, right_data)
    except Exception as e:
        assert str(e) == "Error writing {}: Error reading {}: Error reading {}"
    else:
        assert False

def test_merge_json_cli():
    # Test CLI: merge two JSON files and write the result to a new file
    left_path = Path(tempfile.mkstemp()[1])
    right_path = Path(tempfile.mkstemp()[1])
    output_path = Path(tempfile.mkstemp()[1])

    with open(left_path, 'w', encoding='utf-8') as f:
        json.dump({'a': 1}, f)
    with open(right_path, 'w', encoding='utf-8') as f:
        json.dump({'b': 2}, f)

    subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], str(left_path), str(right_path), str(output_path)], check=True)

    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        merged_data = json.load(f)
    assert merged_data == {'a': 1, 'b': 2}

def test_merge_json_cli_invalid():
    # Test CLI: merge two JSON files and write the result to a new file with conflicting keys
    left_path = Path(tempfile.mkstemp()[1])
    right_path = Path(tempfile.mkstemp()[1])
    output_path = Path(tempfile.mkstemp()[1])

    with open(left_path, 'w', encoding='utf-8') as f:
        json.dump({'a': 1}, f)
    with open(right_path, 'w', encoding='utf-8') as f:
        json.dump({'a': 2}, f)

    subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], str(left_path), str(right_path), str(output_path)], check=True)

    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        merged_data = json.load(f)
    assert merged_data == {'a': 2}

if __name__ == "__main__":
    test_merge_json()
    test_merge_json_invalid()
    test_merge_json_cli()
    test_merge_json_cli_invalid()