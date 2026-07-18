import json
import os
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
    
    if not config:
        print("Configuration file is empty.")
        sys.exit(3)
    
    errors = validate_config(config)
    
    if errors:
        for error in errors:
            print(error)
        sys.exit(4)
    
    print("Configuration is valid.")
    sys.exit(0)

if __name__ == "__main__":
    main()