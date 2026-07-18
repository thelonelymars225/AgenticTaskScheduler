import sys
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("merge_json", CANDIDATE_PATH)
merge_json = importlib.util.module_from_spec(spec).merge_json
spec.loader.exec_module(merge_json)

class TestMergeJson(unittest.TestCase):

    def test_valid_merge(self):
        json1 = '{"key1": "value1", "key2": {"nested_key": "nested_value"}}'
        json2 = '{"key2": {"other_nested_key": "other_nested_value"}, "key3": "value3"}'

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
             tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
            f1.write(json1)
            f1.flush()
            f2.write(json2)
            f2.flush()

            merged_json = merge_json(json.load(f1), json.load(f2))

            self.assertEqual(merged_json, {
                "key1": "value1",
                "key2": {"nested_key": "nested_value", "other_nested_key": "other_nested_value"},
                "key3": "value3"
            })

    def test_invalid_merge(self):
        json1 = '{"key1": "value1"}'
        json2 = '{"key1": "conflicting_value"}'

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
             tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
            f1.write(json1)
            f1.flush()
            f2.write(json2)
            f2.flush()

            merged_json = merge_json(json.load(f1), json.load(f2))

            self.assertEqual(merged_json, {"key1": "conflicting_value"})

    def test_cli(self):
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f1, \
             tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f2:
            f1.write('{"key1": "value1"}')
            f1.flush()
            f2.write('{"key2": "value2"}')
            f2.flush()

            process = subprocess.Popen([sys.executable, CANDIDATE_PATH, f1.name, f2.name],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

            output, error = process.communicate(input=b'',
                                                encoding='utf-8')

            self.assertEqual(process.returncode, 0)
            self.assertIn('{"key1": "value1", "key2": "value2"}', output)

if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])