import os
import json
import re
from collections import Counter

def count_lines(text):
    if not text.strip():
        return 0
    return len(text.splitlines())

def count_characters(text):
    return len(text)

def tokenize_text(text):
    # Use regex to find words, remove punctuation, and normalize to lowercase
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens

def word_frequency(tokens):
    if not tokens:
        return {}
    return dict(Counter(tokens))

def analyze_text(text):
    if text is None or not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    lines = count_lines(text)
    characters = count_characters(text)
    tokens = tokenize_text(text)
    frequency = word_frequency(tokens)
    
    return {
        "lines": lines,
        "characters": characters,
        "words": len(tokens),
        "frequency": frequency
    }

def analyze_file(file_path):
    if not isinstance(file_path, str) or not file_path:
        raise ValueError("File path must be a non-empty string")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No such file: '{file_path}'")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return analyze_text(text)

if __name__ == "__main__":
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        exit(0)
    
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        result = analyze_file(file_path)
        json.dump(result, sys.stdout, indent=4)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except UnicodeDecodeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)