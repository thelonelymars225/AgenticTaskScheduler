import json
import os
import importlib.util
from tempfile import NamedTemporaryFile, TemporaryDirectory

# Load the candidate module from its path in the environment variable CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_merge_json():
    # Test valid case: merge two JSON objects with no conflicts
    json1 = {'a': 1, 'b': 2}
    json2 = {'c': 3, 'd': 4}
    merged = candidate_module.merge_json(json1, json2)
    assert merged == {'a': 1, 'b': 2, 'c': 3, 'd': 4}

    # Test invalid case: merge two JSON objects with conflicting scalar values
    json1 = {'a': 1}
    json2 = {'a': 2}
    merged = candidate_module.merge_json(json1, json2)
    assert merged == {'a': 2}  # Candidate should choose the second value

def test_cli():
    # Create temporary input files for the CLI
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f1, \
         NamedTemporaryFile(mode='w', encoding='utf-8') as f2:
        json.dump({'a': 1, 'b': 2}, f1)
        json.dump({'c': 3, 'd': 4}, f2)

        # Run the CLI with the temporary input files
        os.environ['CANDIDATE_PATH'] = candidate_module.__file__
        sys.argv = ['merge_json.py', f1.name, f2.name]
        candidate_module.main()

        # Check that the merged JSON file was created correctly
        with open('merged.json', 'r', encoding='utf-8') as f_out:
            merged_json = json.load(f_out)
            assert merged_json == {'a': 1, 'b': 2, 'c': 3, 'd': 4}

if __name__ == "__main__":
    test_merge_json()
    test_cli()