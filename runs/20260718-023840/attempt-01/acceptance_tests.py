import importlib.util
import json
import os
import sys

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_validate_config():
    # Test valid case
    config = {
        'name': 'Test Config',
        'description': 'This is a test configuration.',
        'min_age': 18,
        'max_users': 1000,
        'is_active': True,
        'allow_anonymous': False
    }
    errors = candidate_module.validate_config(config)
    assert not errors

    # Test invalid case (missing field)
    config = {
        'name': '',
        'description': 'This is a test configuration.',
        'min_age': 18,
        'max_users': 1000,
        'is_active': True,
        'allow_anonymous': False
    }
    errors = candidate_module.validate_config(config)
    assert len(errors) == 1

if __name__ == "__main__":
    test_validate_config()