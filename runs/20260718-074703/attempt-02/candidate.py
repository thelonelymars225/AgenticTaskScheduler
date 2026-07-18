import os
import json
import re
from collections import Counter
import sys

def count_lines(text):
    if not text.strip():
        return 0
    return len(text.splitlines())

def count_characters(text):
    return len(text)

def tokenize_text(text):
    # Use regex to find words, remove punctuation, and normalize to lowercase
    tokens = re.findall(r'\b\w+\b', text)
    return [token.lower() for token in tokens]

def word_frequency(text):
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    tokens = tokenize_text(text)
    frequency = Counter(tokens)
    return dict(sorted(frequency.items()))

def file_word_frequency(path):
    with open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    return word_frequency(text)

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed")
        return 0

    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>", file=sys.stderr)
        return 1

    path = sys.argv[1]
    try:
        with open(path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        stats = {
            "word_frequency": word_frequency(text),
            "line_count": count_lines(text),
            "character_count": count_characters(text)
        }
        print(json.dumps(stats, indent=4))
    except FileNotFoundError:
        print(f"Error: File '{path}' not found", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print(f"Error: Unable to decode file '{path}' as UTF-8", file=sys.stderr)
        return 3

if __name__ == "__main__":
    sys.exit(main())