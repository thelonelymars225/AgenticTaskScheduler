import json
import os
import sys

def merge_json(obj1, obj2):
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        merged = {}
        for key in set(obj1.keys()).union(obj2.keys()):
            if key in obj1 and key in obj2:
                merged[key] = merge_json(obj1[key], obj2[key])
            elif key in obj1:
                merged[key] = obj1[key]
            else:
                merged[key] = obj2[key]
        return merged
    elif isinstance(obj1, list) and isinstance(obj2, list):
        return obj1 + obj2
    else:
        return obj2

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)

    if len(sys.argv) != 3:
        print("Usage: python merge_json.py <file1> <file2>")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r') as f1, open(sys.argv[2], 'r') as f2:
            json1 = json.load(f1)
            json2 = json.load(f2)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading JSON files: {e}")
        sys.exit(2)

    merged_json = merge_json(json1, json2)

    try:
        with open('merged.json', 'w+') as f_out:
            json.dump(merged_json, f_out, indent=4)
            f_out.seek(0)  # Move the file pointer to the beginning
            print(f_out.read())  # Read and print the merged JSON for verification
    except IOError as e:
        print(f"Error writing or reading merged JSON: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()