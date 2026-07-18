import json
import importlib.util
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
import subprocess

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("config_validator", CANDIDATE_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

def test_valid_config():
    config_path = NamedTemporaryFile(mode='w+', encoding='utf-8').name
    with open(config_path, 'w') as f:
        json.dump({
            "name": "example",
            "description": "This is an example configuration.",
            "min_age": 18,
            "max_users": 1000,
            "is_active": True,
            "allow_anonymous": False
        }, f)

    result = subprocess.run([sys.executable, CANDIDATE_PATH, config_path], capture_output=True)
    assert result.returncode == 0

def test_invalid_config():
    config_path = NamedTemporaryFile(mode='w+', encoding='utf-8').name
    with open(config_path, 'w') as f:
        json.dump({
            "min_age": "twenty",
            "max_users": 1001,
            "is_active": "true"
        }, f)

    result = subprocess.run([sys.executable, CANDIDATE_PATH, config_path], capture_output=True)
    assert result.returncode == 3

def test_invalid_file():
    invalid_config_path = NamedTemporaryFile(mode='w+', encoding='utf-8').name
    with open(invalid_config_path, 'w') as f:
        json.dump("not a valid JSON", f)

    result = subprocess.run([sys.executable, CANDIDATE_PATH, invalid_config_path], capture_output=True)
    assert result.returncode == 2

def test_missing_file():
    missing_config_path = NamedTemporaryFile(mode='w+', encoding='utf-8').name
    with open(missing_config_path, 'w') as f:
        json.dump({}, f)

    os.remove(missing_config_path)

    result = subprocess.run([sys.executable, CANDIDATE_PATH, missing_config_path], capture_output=True)
    assert result.returncode == 2

def test_empty_argv():
    result = subprocess.run([sys.executable, CANDIDATE_PATH])
    assert result.returncode == 1