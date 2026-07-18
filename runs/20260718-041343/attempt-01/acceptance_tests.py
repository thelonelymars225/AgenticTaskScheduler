import sys
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("config_validator", CANDIDATE_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

class TestConfigValidator(unittest.TestCase):

    def test_valid_config(self):
        config_path = pathlib.Path(tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name)
        with open(config_path, 'w') as f:
            json.dump({
                "name": "example",
                "description": "This is an example configuration.",
                "min_age": 18,
                "max_users": 1000,
                "is_active": True,
                "allow_anonymous": False
            }, f)
        result = subprocess.run([sys.executable, CANDIDATE_PATH, config_path], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_invalid_config(self):
        config_path = pathlib.Path(tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name)
        with open(config_path, 'w') as f:
            json.dump({
                "min_age": 150,
                "max_users": -1
            }, f)
        result = subprocess.run([sys.executable, CANDIDATE_PATH, config_path], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3)

if __name__ == "__main__":
    unittest.main(argv=[os.path.basename(__file__)])