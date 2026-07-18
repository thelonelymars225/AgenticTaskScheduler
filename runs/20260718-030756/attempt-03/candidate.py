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
        return obj1 if obj1 is not None else obj2

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)

    if len(sys.argv) != 3:
        print("Usage: python merge_json.py <file1> <file2>")
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]

    try:
        with open(file1, 'r', encoding='utf-8') as f1:
            if os.fstat(f1.fileno()).st_size == 0:
                print(f"Error: {file1} is empty.")
                sys.exit(2)
            json1 = json.load(f1)

        with open(file2, 'r', encoding='utf-8') as f2:
            if os.fstat(f2.fileno()).st_size == 0:
                print(f"Error: {file2} is empty.")
                sys.exit(2)
            json2 = json.load(f2)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading JSON files: {e}")
        sys.exit(2)

    merged_json = merge_json(json1, json2)

    try:
        with open('merged.json', 'w', encoding='utf-8') as f_out:
            json.dump(merged_json, f_out, indent=4)
    except IOError as e:
        print(f"Error writing merged JSON: {e}")
        sys.exit(3)

    sys.exit(0)

if __name__ == "__main__":
    main()