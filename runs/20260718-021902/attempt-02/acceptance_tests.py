import importlib.util
import json
import os
import sys

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("config_validator", CANDIDATE_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

def test_valid_config():
    config = {
        'name': 'Test Config',
        'description': 'This is a test configuration',
        'min_age': 18,
        'max_users': 1000,
        'active': True,
        'enabled': False
    }
    
    errors = validator.validate_config(config)
    assert not errors

def test_invalid_config():
    config = {
        'name': '',
        'description': 'This is a test configuration',
        'min_age': -1,
        'max_users': 1000,
        'active': True,
        'enabled': False
    }
    
    errors = validator.validate_config(config)
    assert len(errors) == 2

def test_empty_config():
    config = {}
    
    errors = validator.validate_config(config)
    assert len(errors) == 4

def test_invalid_json():
    config_file = 'invalid.json'
    with open(config_file, 'w') as f:
        f.write('Invalid JSON')
    
    try:
        validator.main([config_file])
        assert False
    except SystemExit as e:
        assert e.code == 2

def test_missing_config_file():
    config_file = 'missing.json'
    
    try:
        validator.main([config_file])
        assert False
    except SystemExit as e:
        assert e.code == 3

if __name__ == "__main__":
    test_valid_config()
    test_invalid_config()
    test_empty_config()
    test_invalid_json()
    test_missing_config_file()