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
        config_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name
        with open(config_file, 'w') as f:
            json.dump({
                "name": "example",
                "description": "This is an example configuration.",
                "min_age": 18,
                "max_users": 1000,
                "is_active": True,
                "allow_anonymous": False
            }, f)
        subprocess.run([sys.executable, CANDIDATE_PATH, config_file], check=True, input=None)
        self.assertEqual(subprocess.run([sys.executable, CANDIDATE_PATH, config_file], check=False, capture_output=True).returncode, 0)

    def test_invalid_config(self):
        config_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name
        with open(config_file, 'w') as f:
            json.dump({
                "min_age": 150,
                "max_users": -1,
                "is_active": "true",
                "allow_anonymous": "false"
            }, f)
        subprocess.run([sys.executable, CANDIDATE_PATH, config_file], check=False, capture_output=True).returncode != 0

    def test_empty_config(self):
        config_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name
        with open(config_file, 'w') as f:
            json.dump({}, f)
        subprocess.run([sys.executable, CANDIDATE_PATH, config_file], check=False, capture_output=True).returncode != 0

    def test_invalid_config_file(self):
        config_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name
        with open(config_file, 'w') as f:
            f.write("Invalid JSON")
        subprocess.run([sys.executable, CANDIDATE_PATH, config_file], check=False, capture_output=True).returncode != 0

if __name__ == "__main__":
    unittest.main(argv=[os.path.basename(__file__)])