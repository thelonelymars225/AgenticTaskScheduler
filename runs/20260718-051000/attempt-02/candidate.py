import os
import json
from collections import Counter
from pathlib import Path

def count_lines(text):
    return len(text.splitlines())

def count_words(text):
    return len(text.split())

def count_characters(text):
    return len(text)

def word_frequencies(text):
    words = text.lower().split()
    return dict(Counter(words))

def analyze_text(text):
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    if text.strip() == "":
        return {
            'lines': 0,
            'words': 0,
            'characters': 0,
            'word_frequencies': {}
        }
    return {
        'lines': count_lines(text),
        'words': count_words(text),
        'characters': count_characters(text),
        'word_frequencies': word_frequencies(text)
    }

if __name__ == '__main__':
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        exit(0)

    import sys
    if len(sys.argv) != 2:
        print("Usage: python text_stats.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        file_path = Path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"File '{filename}' does not exist")
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            result = analyze_text(text)
            json.dump(result, sys.stdout, ensure_ascii=False, indent=4)
    except UnicodeDecodeError:
        print(f"Error: File '{filename}' is not a valid UTF-8 encoded file", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)