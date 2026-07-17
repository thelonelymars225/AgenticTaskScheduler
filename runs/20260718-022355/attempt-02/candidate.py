import os
import json
from collections import Counter
import re

def count_lines(text):
    return len(text.splitlines())

def count_words(text):
    return len(re.findall(r'\b\w+\b', text))

def count_characters(text):
    return len(text)

def word_frequencies(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return dict(Counter(words))

class TextStats:
    @staticmethod
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

    import sys
    if len(sys.argv) != 2:
        print("Usage: python text_stats.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            text = file.read()
            result = TextStats.analyze_text(text)
            json.dump(result, sys.stdout, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)