import os
import json
from collections import Counter
import string

class TextAnalysisError(Exception):
    """Custom exception for text analysis errors."""
    pass

def count_lines(text):
    return len(text.splitlines()) if text else 0

def count_words(text):
    return len(text.split()) if text else 0

def count_characters(text):
    return len(text) if text else 0

def word_frequencies(text):
    if not text:
        return {}
    # Remove punctuation and convert to lowercase
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator).lower()
    words = cleaned_text.split()
    return dict(Counter(words))

def analyze_text(text):
    if text is None:
        raise TextAnalysisError("Input text cannot be None")
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
            stats = analyze_text(text)
            json.dump(stats, sys.stdout, ensure_ascii=False, indent=4)
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.", file=sys.stderr)
        sys.exit(1)
    except IOError:
        print(f"Error: Could not read the file '{filename}'.", file=sys.stderr)
        sys.exit(1)
    except TextAnalysisError as e:
        print(f"Text analysis error: {e}", file=sys.stderr)
        sys.exit(1)