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
        config = {
            'name': 'Test Config',
            'description': 'This is a test configuration.',
            'min_age': 18,
            'max_users': 100,
            'is_active': True,
            'allow_anonymous': False
        }

        errors = validator.validate_config(config)
        self.assertEqual(errors, [])

    def test_invalid_config(self):
        config = {
            'name': '',
            'description': 'This is a test configuration.',
            'min_age': 150,
            'max_users': -1,
            'is_active': True,
            'allow_anonymous': False
        }

        errors = validator.validate_config(config)
        self.assertEqual(len(errors), 3)

    def test_invalid_json(self):
        config_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name
        with open(config_file, 'w') as f:
            f.write('Invalid JSON')

        try:
            subprocess.run([sys.executable, CANDIDATE_PATH, config_file], check=True)
            self.fail("Expected non-zero exit code")
        except subprocess.CalledProcessError:
            pass

    def test_missing_config_file(self):
        try:
            subprocess.run([sys.executable, CANDIDATE_PATH, 'non_existent_file.json'], check=True)
            self.fail("Expected non-zero exit code")
        except subprocess.CalledProcessError:
            pass

if __name__ == "__main__":
    unittest.main(argv=[os.path.basename(__file__)])