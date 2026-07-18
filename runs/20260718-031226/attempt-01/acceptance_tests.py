import importlib.util
import os
import pathlib
import subprocess
import tempfile
import unittest

class TestLogSummarizer(unittest.TestCase):
    def setUp(self):
        self.candidate_path = os.environ['CANDIDATE_PATH']
        spec = importlib.util.spec_from_file_location('candidate', self.candidate_path)
        self.candidate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.candidate_module)

    def test_summarize_empty_input(self):
        summary = self.candidate_module.summarize([])
        self.assertEqual(summary, {'': 0})

    def test_summarize_single_level(self):
        log_lines = ['INFO: message']
        summary = self.candidate_module.summarize(log_lines)
        self.assertEqual(summary, {'INFO': 1})

    def test_summarize_multiple_levels(self):
        log_lines = [
            'DEBUG: message',
            'INFO: message',
            'WARNING: message',
            'ERROR: message'
        ]
        summary = self.candidate_module.summarize(log_lines)
        self.assertEqual(summary, {
            'DEBUG': 1,
            'INFO': 1,
            'WARNING': 1,
            'ERROR': 1
        })

    def test_summarize_empty_line(self):
        log_lines = ['']
        summary = self.candidate_module.summarize(log_lines)
        self.assertEqual(summary, {'': 1})

    def test_cli_input(self):
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write('INFO: message\n')
            tmp_file.flush()
            subprocess.run([self.candidate_path], stdin=tmp_file.name)
            with open(tmp_file.name, 'r', encoding='utf-8') as output_file:
                summary = json.load(output_file)
        self.assertEqual(summary, {'INFO': 1})

    def test_cli_empty_input(self):
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as tmp_file:
            subprocess.run([self.candidate_path], stdin=tmp_file.name)
            with open(tmp_file.name, 'r', encoding='utf-8') as output_file:
                summary = json.load(output_file)
        self.assertEqual(summary, {'': 0})

if __name__ == '__main__':
    unittest.main()