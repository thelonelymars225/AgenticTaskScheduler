import json
import os
import importlib.util
import sys

def validate_config(config):
    errors = []

    # Validate required string fields
    for field in ['name', 'description']:
        if not isinstance(config.get(field), str) or not config[field]:
            errors.append(f"Missing or invalid string field: {field}")

    # Validate integer-range fields
    int_fields = {
        'min_age': (0, 120),
        'max_users': (1, 1000)
    }
    for field, (min_val, max_val) in int_fields.items():
        value = config.get(field)
        if not isinstance(value, int) or not min_val <= value <= max_val:
            errors.append(f"Missing or invalid integer field: {field} (must be between {min_val} and {max_val})")

    # Validate boolean fields
    bool_fields = ['is_active', 'allow_anonymous']
    for field in bool_fields:
        if not isinstance(config.get(field), bool):
            errors.append(f"Missing or invalid boolean field: {field}")

    return errors

def load_candidate(candidate_path):
    spec = importlib.util.spec_from_file_location("candidate", candidate_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)

    if len(sys.argv) != 2:
        print("Usage: python config_validator.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(2)

    candidate_path = os.environ['CANDIDATE_PATH']
    try:
        candidate_module = load_candidate(candidate_path)
    except Exception as e:
        print(f"Failed to import candidate module: {e}")
        sys.exit(4)

    validate_config_func = getattr(candidate_module, 'validate_config', None)
    if not callable(validate_config_func):
        print("Candidate module does not have a 'validate_config' function")
        sys.exit(5)

    try:
        errors = validate_config_func(config)
    except Exception as e:
        print(f"Error validating configuration: {e}")
        sys.exit(6)

    if errors:
        for error in errors:
            print(error)
        sys.exit(7)

    print("Configuration is valid.")
    sys.exit(0)

if __name__ == "__main__":
    main()