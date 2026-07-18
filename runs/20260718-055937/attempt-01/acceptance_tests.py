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
            'name': 'example',
            'description': 'This is an example configuration.',
            'timeout': 30,
            'retries': 5,
            'enabled': True,
            'debug': False
        }

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            json.dump(config, f)
            f.flush()

            result = subprocess.run([sys.executable, CANDIDATE_PATH, f.name], capture_output=True, text=True)

            self.assertEqual(result.returncode, 0)
            self.assertIn('Configuration is valid.', result.stdout)

    def test_invalid_config(self):
        config = {
            'name': '',
            'description': 'This is an example configuration.',
            'timeout': 30,
            'retries': 5,
            'enabled': True,
            'debug': False
        }

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            json.dump(config, f)
            f.flush()

            result = subprocess.run([sys.executable, CANDIDATE_PATH, f.name], capture_output=True, text=True)

            self.assertEqual(result.returncode, 3)
            self.assertIn('Missing or invalid string field: name', result.stderr)

    def test_invalid_config_file(self):
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            f.write('Invalid JSON')
            f.flush()

            result = subprocess.run([sys.executable, CANDIDATE_PATH, f.name], capture_output=True, text=True)

            self.assertEqual(result.returncode, 2)
            self.assertIn('Error reading configuration file:', result.stderr)

if __name__ == "__main__":
    unittest.main(argv=[os.path.basename(__file__)])