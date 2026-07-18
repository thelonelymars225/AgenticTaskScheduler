import importlib.util
import json
import os
import pathlib
import subprocess
import sys

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("merge_json", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_merge_valid():
    # Create valid JSON fixtures
    left_data_path = pathlib.Path('left.json')
    right_data_path = pathlib.Path('right.json')

    with left_data_path.open('w', encoding='utf-8') as f:
        json.dump({'a': 1, 'b': {'c': 2}}, f)

    with right_data_path.open('w', encoding='utf-8') as f:
        json.dump({'b': {'d': 3}, 'e': 4}, f)

    # Run candidate with valid inputs
    output_path = pathlib.Path('output.json')
    result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], str(left_data_path), str(right_data_path), str(output_path)],
                           capture_output=True,
                           text=True,
                           input='')

    # Check that candidate wrote valid JSON to output
    with output_path.open('r', encoding='utf-8') as f:
        merged_data = json.load(f)
        assert merged_data == {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}

def test_merge_invalid():
    # Create invalid JSON fixtures
    left_data_path = pathlib.Path('left.json')
    right_data_path = pathlib.Path('right.json')

    with left_data_path.open('w', encoding='utf-8') as f:
        json.dump({'a': 1, 'b': {'c': 2}}, f)

    with right_data_path.open('w', encoding='utf-8') as f:
        json.dump({'b': {'d': 3}, 'e': 4}, f)
        # Introduce a syntax error in the JSON
        f.write('\n invalid')

    # Run candidate with invalid inputs
    output_path = pathlib.Path('output.json')
    result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], str(left_data_path), str(right_data_path), str(output_path)],
                           capture_output=True,
                           text=True,
                           input='')

    # Check that candidate reports error on stderr
    assert 'Error reading' in result.stderr

def test_merge_type_mismatch():
    # Create valid JSON fixtures with type mismatch
    left_data_path = pathlib.Path('left.json')
    right_data_path = pathlib.Path('right.json')

    with left_data_path.open('w', encoding='utf-8') as f:
        json.dump({'a': 1, 'b': {'c': 2}}, f)

    with right_data_path.open('w', encoding='utf-8') as f:
        json.dump({'b': {'d': 3}, 'e': '4'}, f)  # Introduce a type mismatch

    # Run candidate with valid inputs
    output_path = pathlib.Path('output.json')
    result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], str(left_data_path), str(right_data_path), str(output_path)],
                           capture_output=True,
                           text=True,
                           input='')

    # Check that candidate wrote valid JSON to output
    with output_path.open('r', encoding='utf-8') as f:
        merged_data = json.load(f)
        assert merged_data == {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': '4'}

if __name__ == "__main__":
    test_merge_valid()
    test_merge_invalid()
    test_merge_type_mismatch()