import importlib.util
import json
import os
import pathlib
import sys
from tempfile import NamedTemporaryFile

# Load candidate from file
spec = importlib.util.spec_from_file_location("candidate", os.environ['CANDIDATE_PATH'])
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

def test_validate_config_valid():
    config = {
        'name': 'example',
        'description': 'This is an example configuration.',
        'timeout': 30,
        'retries': 5,
        'enabled': True,
        'debug': False
    }
    
    errors = candidate_module.validate_config(config)
    assert not errors

def test_validate_config_invalid():
    config = {
        'name': '',
        'description': 'This is an example configuration.',
        'timeout': 700,  # timeout should be between 10 and 600
        'retries': 15,   # retries should be between 1 and 10
        'enabled': True,
        'debug': False
    }
    
    errors = candidate_module.validate_config(config)
    assert len(errors) == 2

def test_main_cli():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        config = {
            'name': 'example',
            'description': 'This is an example configuration.',
            'timeout': 30,
            'retries': 5,
            'enabled': True,
            'debug': False
        }
        json.dump(config, f)
        
        # Run main function with temporary config file
        sys.argv = ['python', os.environ['CANDIDATE_PATH'], f.name]
        candidate_module.main()
        
        # Check exit code and output
        assert sys.exitcode == 0

def test_main_cli_invalid():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        config = {
            'name': '',
            'description': 'This is an example configuration.',
            'timeout': 700,  # timeout should be between 10 and 600
            'retries': 15,   # retries should be between 1 and 10
            'enabled': True,
            'debug': False
        }
        json.dump(config, f)
        
        # Run main function with temporary config file
        sys.argv = ['python', os.environ['CANDIDATE_PATH'], f.name]
        candidate_module.main()
        
        # Check exit code and output
        assert sys.exitcode == 3

def test_main_cli_invalid_config_file():
    # Run main function with non-existent config file
    sys.argv = ['python', os.environ['CANDIDATE_PATH'], 'non_existent_file.json']
    candidate_module.main()
    
    # Check exit code and output
    assert sys.exitcode == 2

def test_main_cli_invalid_args():
    # Run main function without config file argument
    sys.argv = ['python', os.environ['CANDIDATE_PATH']]
    candidate_module.main()
    
    # Check exit code and output
    assert sys.exitcode == 1