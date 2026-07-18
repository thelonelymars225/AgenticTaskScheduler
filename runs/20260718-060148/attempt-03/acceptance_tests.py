import os
import sys
from pathlib import Path
import tempfile
import json
import argparse
import importlib.util
import unittest

# Load candidate from file
CANDIDATE_PATH = os.environ['CANDIDATE_PATH']
spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

class TestTextStatistics(unittest.TestCase):

    def test_analyze_text(self):
        # Create a sample text
        text = "This is a sample text.\nIt has multiple lines."
        
        # Analyze the text
        result = candidate_module.analyze_text(text)
        
        # Check if the analysis result contains expected values
        self.assertIn('lines', result)
        self.assertEqual(result['lines'], 2)
        self.assertIn('words', result)
        self.assertEqual(result['words'], 6)
        self.assertIn('characters', result)
        self.assertEqual(result['characters'], 32)
        
    def test_word_frequencies(self):
        # Create a sample text
        text = "This is a sample text.\nIt has multiple lines."
        
        # Analyze the text
        result = candidate_module.analyze_text(text)
        
        # Check if word frequencies are correct
        self.assertIn('word_frequencies', result)
        frequencies = result['word_frequencies']
        self.assertEqual(frequencies['this'], 1)
        self.assertEqual(frequencies['is'], 1)
        self.assertEqual(frequencies['a'], 1)
        self.assertEqual(frequencies['sample'], 1)
        self.assertEqual(frequencies['text'], 2)
        self.assertEqual(frequencies['it'], 1)
        self.assertEqual(frequencies['has'], 1)
        self.assertEqual(frequencies['multiple'], 1)
        self.assertEqual(frequencies['lines'], 1)

    def test_empty_text(self):
        # Create an empty text
        text = ""
        
        # Analyze the text
        result = candidate_module.analyze_text(text)
        
        # Check if analysis result is correct for empty text
        self.assertIn('lines', result)
        self.assertEqual(result['lines'], 0)
        self.assertIn('words', result)
        self.assertEqual(result['words'], 0)
        self.assertIn('characters', result)
        self.assertEqual(result['characters'], 0)

    def test_invalid_file_path(self):
        # Create a sample text
        text = "This is a sample text.\nIt has multiple lines."
        
        # Analyze the text with an invalid file path
        try:
            candidate_module.analyze_text("invalid_file_path")
            self.fail("Expected FileNotFoundError to be raised.")
        except FileNotFoundError:
            pass

    def test_permission_denied(self):
        # Create a sample text
        text = "This is a sample text.\nIt has multiple lines."
        
        # Analyze the text with permission denied error
        try:
            candidate_module.analyze_text("/path/to/permission/denied/file")
            self.fail("Expected PermissionError to be raised.")
        except PermissionError:
            pass

if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]])