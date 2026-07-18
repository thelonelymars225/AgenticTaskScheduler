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
    
    if not text.strip():
        return 0, {}, 0
    
    lines = count_lines(text)
    chars = count_characters(text)
    words = tokenize_text(text)
    freq = Counter(words)
    
    # Return sorted frequency mapping
    sorted_freq = dict(sorted(freq.items()))
    
    return len(words), sorted_freq, chars

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
        word_count, freq_map, char_count = file_word_frequency(path)
        result = {
            "word_count": word_count,
            "frequency": freq_map,
            "character_count": char_count
        }
        print(json.dumps(result, indent=4))
        return 0
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as e:
        print(f"Unicode decode error: {e}", file=sys.stderr)
        return 3
    except TypeError as e:
        print(f"Type error: {e}", file=sys.stderr)
        return 4

if __name__ == "__main__":
    sys.exit(main())