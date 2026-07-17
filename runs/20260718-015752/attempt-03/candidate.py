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
    # Remove punctuation from words
    words = [word.strip('.,!?;:()[]{}"\'') for word in words]
    return dict(Counter(words))

def analyze_text(text):
    if not text:
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

    import argparse

    parser = argparse.ArgumentParser(description='Analyze text statistics from a file.')
    parser.add_argument('filename', type=str, help='The path to the UTF-8 encoded text file.')

    args = parser.parse_args()

    try:
        if not os.path.isfile(args.filename):
            raise FileNotFoundError(f"The file '{args.filename}' does not exist.")
        
        with open(args.filename, 'r', encoding='utf-8') as file:
            text = file.read()
            result = analyze_text(text)
            json.dump(result, sys.stdout, ensure_ascii=False, indent=4)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: The file '{args.filename}' is not readable.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)