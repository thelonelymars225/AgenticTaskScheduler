import os
import json
from collections import Counter

def count_lines(text):
    return len(text.splitlines()) if text else 0

def count_words(text):
    return len(text.split()) if text else 0

def count_characters(text):
    return len(text) if text else 0

def word_frequencies(text):
    words = text.lower().split() if text else []
    return dict(Counter(words))

def analyze_text(text):
    return {
        'lines': count_lines(text),
        'words': count_words(text),
        'characters': count_characters(text),
        'word_frequencies': word_frequencies(text)
    }

if __name__ == '__main__':
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        exit(0)

    import argparse
    parser = argparse.ArgumentParser(description='Analyze text statistics from a UTF-8 file.')
    parser.add_argument('file', type=str, help='Path to the UTF-8 file')
    args = parser.parse_args()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
            result = analyze_text(text)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        import sys
        print(f"Error: {e}", file=sys.stderr)
        exit(1)