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
            'max_users': 1000,
            'is_active': True,
            'allow_anonymous': False
        }
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f:
            json.dump(config, f)
            f.flush()
            
            result = subprocess.run([sys.executable, CANDIDATE_PATH, f.name], capture_output=True, text=True)
            
            self.assertEqual(result.returncode, 0)

    def test_invalid_config(self):
        config = {
            'name': '',
            'description': 'This is a test configuration.',
            'min_age': -1,
            'max_users': 1000000,
            'is_active': True,
            'allow_anonymous': False
        }
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f:
            json.dump(config, f)
            f.flush()
            
            result = subprocess.run([sys.executable, CANDIDATE_PATH, f.name], capture_output=True, text=True)
            
            self.assertEqual(result.returncode, 5)

if __name__ == "__main__":
    unittest.main(argv=[os.path.basename(__file__)])