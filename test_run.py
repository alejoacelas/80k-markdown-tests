"""Offline checks for capture integrity, errors and preservation of previous runs."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import run


class RunnerTests(unittest.TestCase):
    def test_tasks_and_ids(self):
        self.assertEqual(len(run.read_tasks(run.ROOT / 'tasks.tsv')), 30)
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'tasks.tsv'
            for content in ('../bad\tx\thttps://example.org\tp\n',
                            'a\tx\thttps://example.org\tp\na\tx\thttps://example.org\tp\n'):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    run.read_tasks(path)

    def test_capture_preserves_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'calls.jsonl'
            payload = {'tool_name': 'WebFetch', 'tool_input': {'prompt': 'é'},
                       'tool_response': {'result': 'literal response'}}
            subprocess.run([sys.executable, str(run.ROOT / 'capture.py'), str(path)],
                           input=json.dumps(payload), text=True, check=True)
            self.assertEqual(json.loads(path.read_text()), payload)

    def test_existing_run_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)
            sentinel = path / 'keep.txt'
            sentinel.write_text('unchanged')
            with patch.object(sys, 'argv', ['run.py', '--output', directory]), \
                 patch('run.shutil.which', return_value='/bin/example'), \
                 patch('run.subprocess.check_output', return_value='test'), \
                 self.assertRaises(SystemExit) as caught:
                run.main()
            self.assertEqual(caught.exception.code, 2)
            self.assertEqual(sentinel.read_text(), 'unchanged')

    def test_missing_capture_is_error(self):
        task = run.read_tasks(run.ROOT / 'tasks.tsv')[0]
        def fake(command, stdout, stderr, timeout):
            stdout.write_text('{}')
            stderr.write_text('')
            if command[0] == 'curl':
                pathlib.Path(command[command.index('--output') + 1]).write_text('reference')
            return 0
        with tempfile.TemporaryDirectory() as directory, patch('run.execute', side_effect=fake):
            result = run.run_task(task, pathlib.Path(directory), 'test', None, 1)
            self.assertIn('Missing or invalid WebFetch capture', result['errors'])

    def test_timeout_reports_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)
            code = run.execute([sys.executable, '-c', 'import time; time.sleep(5)'],
                               path / 'out', path / 'err', 0.05)
            self.assertEqual(code, 124)
            self.assertIn('Timed out', (path / 'err').read_text())


if __name__ == '__main__':
    unittest.main()
