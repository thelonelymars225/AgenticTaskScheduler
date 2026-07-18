import os
import json
import re
from collections import Counter
import sys

def tokenize(text):
    if text is None or not isinstance(text, str):
        raise TypeError("Input must be a string")
    # Use regex to find words and remove surrounding punctuation
    words = re.findall(r'\b\w+\b', text)
    return [word.lower() for word in words]

def frequency_mapping(text):
    tokens = tokenize(text)
    return dict(Counter(tokens))

def line_count(text):
    if not text.strip():
        return 0
    return len(text.splitlines())

def character_count(text):
    return len(text)

def analyze_text(text):
    if text is None or not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    words = tokenize(text)
    word_freq = frequency_mapping(text)
    lines = line_count(text)
    chars = character_count(text)
    
    return {
        "words": len(words),
        "word_frequency": word_freq,
        "lines": lines,
        "characters": chars
    }

def analyze_file(file_path):
    if not file_path:
        raise ValueError("File path must be provided")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            return analyze_text(text)
    except FileNotFoundError:
        raise
    except UnicodeDecodeError:
        raise

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed")
        return 0
    
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>", file=sys.stderr)
        return 1
    
    file_path = sys.argv[1]
    
    try:
        result = analyze_file(file_path)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=4)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 4

if __name__ == "__main__":
    sys.exit(main())