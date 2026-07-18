import os
import sys
from pathlib import Path
import tempfile
import importlib.util
import subprocess

# Load candidate from CANDIDATE_PATH
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_merge_json():
    # Test valid case: merge two JSON objects with no conflicts
    data1 = {'a': 1, 'b': 2}
    data2 = {'c': 3, 'd': 4}
    merged_data = candidate_module.merge_json(data1, data2)
    assert merged_data == {'a': 1, 'b': 2, 'c': 3, 'd': 4}

def test_merge_json_conflict():
    # Test invalid case: merge two JSON objects with conflicting scalar values
    data1 = {'a': 1}
    data2 = {'a': 2}
    merged_data = candidate_module.merge_json(data1, data2)
    assert merged_data == {'a': 2}

def test_cli_valid():
    # Test CLI: merge two valid JSON files and write the result to a new file
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f2, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f_out:
        json.dump({'a': 1}, f1)
        json.dump({'b': 2}, f2)
        f1.flush()
        f2.flush()
        subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name], stdin=f_out.file, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        f_out.seek(0)
        merged_data = json.load(f_out)
        assert merged_data == {'a': 1, 'b': 2}

def test_cli_invalid():
    # Test CLI: merge two invalid JSON files and check error handling
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f2:
        json.dump({'a': 1}, f1)
        f1.write('invalid JSON')
        f1.flush()
        subprocess.run([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert b"Error reading JSON files: " in subprocess.getoutput([sys.executable, os.environ['CANDIDATE_PATH'], f1.name, f2.name]).encode()

if __name__ == "__main__":
    test_merge_json()
    test_merge_json_conflict()
    test_cli_valid()
    test_cli_invalid()