import os
import sys
from pathlib import Path
import tempfile
import json
import importlib.util
import unittest

# Load candidate from CANDIDATE_PATH
CANDIDATE_PATH = os.environ['CANDIDATE_PATH']
spec = importlib.util.spec_from_file_location("text_stats", CANDIDATE_PATH)
text_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(text_stats)

class TestTextStats(unittest.TestCase):

    def test_analyze_text_valid(self):
        # Create a temporary file with some text
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
            tmp.write("This is a sample text.\n")
            tmp.write("It has multiple lines and words.")
            tmp.flush()
            
            # Analyze the text
            stats = text_stats.analyze_text(tmp.read())
            
            # Check if the analysis results are correct
            self.assertEqual(stats['lines'], 2)
            self.assertEqual(stats['words'], 7)
            self.assertEqual(stats['characters'], 43)
            
            # Check word frequencies
            self.assertIn('this', stats['word_frequencies'])
            self.assertIn('is', stats['word_frequencies'])
            self.assertIn('a', stats['word_frequencies'])
            self.assertIn('sample', stats['word_frequencies'])
            self.assertIn('text', stats['word_frequencies'])
            self.assertEqual(stats['word_frequencies']['this'], 1)
            
    def test_analyze_text_invalid(self):
        # Test with empty text
        stats = text_stats.analyze_text("")
        
        # Check if the analysis results are correct for empty text
        self.assertEqual(stats['lines'], 0)
        self.assertEqual(stats['words'], 0)
        self.assertEqual(stats['characters'], 0)
        
    def test_analyze_text_none(self):
        with self.assertRaises(text_stats.TextAnalysisError):
            text_stats.analyze_text(None)

if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]])