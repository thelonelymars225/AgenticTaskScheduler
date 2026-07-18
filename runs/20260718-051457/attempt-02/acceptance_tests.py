import os
import sys
from pathlib import Path
import tempfile
import importlib.util
import subprocess

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("merge_json", CANDIDATE_PATH)
merge_json = importlib.util.module_from_spec(spec).merge_json
spec.loader.exec_module(module=merge_json)

def test_merge_json_valid():
    json1 = '{"key1": "value1"}'
    json2 = '{"key2": "value2"}'
    expected_output = '{"key1": "value1", "key2": "value2"}'

    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        f1.write(json1)
        f1.flush()
        f2.write(json2)
        f2.flush()

        subprocess.run([sys.executable, CANDIDATE_PATH, f1.name, f2.name],
                       capture_output=True,
                       text=True)

        with open('merged.json', 'r') as f_out:
            output = f_out.read()
            assert output == expected_output

def test_merge_json_invalid():
    json1 = '{"key1": "value1"}'
    json2 = '{"key1": "conflicting value"}'

    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        f1.write(json1)
        f1.flush()
        f2.write(json2)
        f2.flush()

        subprocess.run([sys.executable, CANDIDATE_PATH, f1.name, f2.name],
                       capture_output=True,
                       text=True)

        with open('merged.json', 'r') as f_out:
            output = f_out.read()
            assert output == '{"key1": "conflicting value"}'

def test_merge_json_invalid_input():
    json1 = '{"key1": "value1"}'
    json2 = 123

    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
         tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
        f1.write(json1)
        f1.flush()
        f2.write(str(json2))
        f2.flush()

        try:
            subprocess.run([sys.executable, CANDIDATE_PATH, f1.name, f2.name],
                           capture_output=True,
                           text=True)
            assert False
        except subprocess.CalledProcessError as e:
            assert e.returncode == 3

if __name__ == "__main__":
    test_merge_json_valid()
    test_merge_json_invalid()
    test_merge_json_invalid_input()