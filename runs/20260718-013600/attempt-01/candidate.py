import os
import json
from collections import Counter

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
        'lines': count_lines(text),
        'words': count_words(text),
        'characters': count_characters(text),
        'frequencies': word_frequencies(text)
    }

if __name__ == '__main__':
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        # Run a safe non-interactive self-check
        test_text = "Hello world! Hello Python."
        result = analyze_text(test_text)
        expected_result = {
            'lines': 1,
            'words': 4,
            'characters': 23,
            'frequencies': {'hello': 2, 'world!': 1, 'python.': 1}
        }
        assert result == expected_result, f"Test failed: {result} != {expected_result}"
        exit(0)

    import sys
    if len(sys.argv) != 2:
        print("Usage: python text_stats.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            text = file.read()
            result = analyze_text(text)
            json.dump(result, sys.stdout, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)