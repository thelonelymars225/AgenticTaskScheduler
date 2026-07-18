import importlib.util
import json
import os
import pathlib
import subprocess
import sys

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("merge_json", os.environ['CANDIDATE_PATH'])
merge_json = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_json)

def test_merge_valid():
    # Create valid JSON fixtures
    left_path = pathlib.Path('left.json')
    right_path = pathlib.Path('right.json')

    with left_path.open('w', encoding='utf-8') as f:
        json.dump({'a': 1, 'b': {'c': 2}}, f)

    with right_path.open('w', encoding='utf-8') as f:
        json.dump({'b': {'d': 3}, 'e': 4}, f)

    # Run candidate
    output_path = pathlib.Path('output.json')
    subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], str(left_path), str(right_path), str(output_path)], check=True)

    # Verify output
    with output_path.open('r', encoding='utf-8') as f:
        merged_data = json.load(f)
        assert merged_data == {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}

def test_merge_invalid():
    # Create invalid JSON fixtures
    left_path = pathlib.Path('left.json')
    right_path = pathlib.Path('right.json')

    with left_path.open('w', encoding='utf-8') as f:
        json.dump({'a': 1, 'b': {'c': 2}}, f)

    with right_path.open('w', encoding='utf-8') as f:
        json.dump({'b': {'d': 3}, 'e': 4}, f)
        f.write('\n')  # Add newline to make JSON invalid

    # Run candidate
    output_path = pathlib.Path('output.json')
    result = subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], str(left_path), str(right_path), str(output_path)], check=False)

    # Verify error message
    with left_path.open('r', encoding='utf-8') as f:
        error_message = f.read()
        assert 'Error reading' in error_message

if __name__ == "__main__":
    test_merge_valid()
    test_merge_invalid()