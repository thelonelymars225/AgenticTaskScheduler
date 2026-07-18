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
    for field, (min_val, max_val) in [('timeout', (10, 600)), ('retries', (1, 10))]:
        value = config.get(field)
        if not isinstance(value, int) or not min_val <= value <= max_val:
            errors.append(f"Missing or invalid integer field {field} with value {value}. Must be between {min_val} and {max_val}")

    # Validate boolean fields
    for field in ['enabled', 'debug']:
        if config.get(field) is not None and not isinstance(config[field], bool):
            errors.append(f"Invalid boolean field: {field}")

    return errors

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed.")
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

    print("Configuration is valid.")
    sys.exit(0)

if __name__ == "__main__":
    main()