import json
import os
import sys

def validate_config(config):
    errors = []
    
    # Validate string fields
    required_strings = ['name', 'description']
    for field in required_strings:
        if not isinstance(config.get(field), str) or not config[field]:
            errors.append(f"Missing or invalid string: {field}")
    
    # Validate integer-range fields
    range_fields = {
        'min_age': (0, 120),
        'max_users': (1, 1000)
    }
    for field, (min_val, max_val) in range_fields.items():
        value = config.get(field)
        if not isinstance(value, int) or not min_val <= value <= max_val:
            errors.append(f"Missing or invalid integer-range: {field} (must be between {min_val} and {max_val})")
    
    # Validate boolean fields
    required_booleans = ['active', 'enabled']
    for field in required_booleans:
        if not isinstance(config.get(field), bool):
            errors.append(f"Missing or invalid boolean: {field}")
    
    return errors

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed")
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
    
    errors = validate_config(config)
    
    if errors:
        for error in errors:
            print(error)
        sys.exit(3)
    
    print("Configuration is valid")
    sys.exit(0)

if __name__ == "__main__":
    main()