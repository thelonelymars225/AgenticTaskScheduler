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
        config_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8').name
        with open(config_file, 'w') as f:
            json.dump({
                "name": "Test Config",
                "description": "This is a test configuration.",
                "min_age": 18,
                "max_users": 1000,
                "is_active": True,
                "allow_anonymous": False
            }, f)
        
        result = subprocess.run([sys.executable, CANDIDATE_PATH, config_file], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_invalid_config(self):
        config_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8').name
        with open(config_file, 'w') as f:
            json.dump({
                "min_age": 18,
                "max_users": 1000,
                "is_active": True,
                "allow_anonymous": False
            }, f)
        
        result = subprocess.run([sys.executable, CANDIDATE_PATH, config_file], capture_output=True, text=True)
        self.assertEqual(result.returncode, 4)

if __name__ == "__main__":
    unittest.main(argv=[os.path.basename(__file__)])