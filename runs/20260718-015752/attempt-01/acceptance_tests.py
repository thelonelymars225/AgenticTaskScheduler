import importlib.util
import json
import os
import unittest
from tempfile import NamedTemporaryFile
from io import StringIO

def load_candidate():
    spec = importlib.util.spec_from_file_location("text_stats", os.environ['CANDIDATE_PATH'])
    return importlib.util.module_from_spec(spec)

class TestTextStats(unittest.TestCase):

    def test_analyze_text(self):
        candidate = load_candidate()
        self.assertIn('analyze_text', dir(candidate))

        text = "Hello, World!\nThis is a test."
        result = candidate.analyze_text(text)
        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['words'], 5)
        self.assertEqual(result['characters'], 24)
        frequencies = result['word_frequencies']
        self.assertIn('hello', frequencies)
        self.assertIn('world', frequencies)
        self.assertIn('this', frequencies)
        self.assertIn('is', frequencies)
        self.assertIn('a', frequencies)
        self.assertIn('test', frequencies)

    def test_empty_text(self):
        candidate = load_candidate()
        self.assertIn('analyze_text', dir(candidate))

        text = ""
        result = candidate.analyze_text(text)
        self.assertEqual(result['lines'], 0)
        self.assertEqual(result['words'], 0)
        self.assertEqual(result['characters'], 0)
        frequencies = result['word_frequencies']
        self.assertEqual(len(frequencies), 0)

    def test_invalid_filename(self):
        candidate = load_candidate()
        self.assertIn('analyze_text', dir(candidate))

        filename = "non_existent_file.txt"
        with NamedTemporaryFile() as file:
            file.write(b"Hello, World!")
            file.flush()

            sys_stdout = StringIO()
            sys_stderr = StringIO()
            os.environ['CANDIDATE_PATH'] = file.name
            import sys
            try:
                candidate.analyze_text(filename)
            except Exception as e:
                self.assertIn("Error:", str(e))
            else:
                self.fail("Expected exception not raised")

    def test_json_output(self):
        candidate = load_candidate()
        self.assertIn('analyze_text', dir(candidate))

        text = "Hello, World!\nThis is a test."
        result = candidate.analyze_text(text)
        json_output = json.dumps(result, ensure_ascii=False, indent=4)
        sys_stdout = StringIO()
        sys_stderr = StringIO()
        os.environ['CANDIDATE_PATH'] = os.path.join(os.getcwd(), 'text_stats.py')
        import sys
        try:
            candidate.analyze_text(text)
        except Exception as e:
            self.assertIn("Error:", str(e))
        else:
            self.assertEqual(sys_stdout.getvalue().strip(), json_output)

if __name__ == '__main__':
    unittest.main(argv=[os.path.basename(__file__)])