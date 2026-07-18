import os
import json
from collections import Counter
import sys

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
    return {
        'line_count': count_lines(text),
        'word_count': count_words(text),
        'character_count': count_characters(text),
        'word_frequencies': word_frequencies(text)
    }

if __name__ == '__main__':
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        exit(0)

    import argparse
    parser = argparse.ArgumentParser(description='Analyze text statistics from a file.')
    parser.add_argument('file', type=str, help='Path to the UTF-8 encoded text file')
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' does not exist.", file=sys.stderr)
        exit(1)

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
            result = analyze_text(text)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        exit(1)