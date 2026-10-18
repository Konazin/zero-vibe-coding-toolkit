"""Regression tests for Zero Toolkit's non-destructive CLI contracts."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / 'zeroctl.py'


class ZeroCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(CLI), *map(str, args)],
                              capture_output=True, text=True, timeout=15)

    def test_doctor_json_is_read_only(self):
        (self.root / 'package.json').write_text('{}')
        result = self.run_cli('doctor', self.root, '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Node/Frontend', json.loads(result.stdout)['stacks'])
        self.assertFalse((self.root / '.zero').exists())

    def test_init_dry_run_then_apply(self):
        preview = self.run_cli('init', self.root, '--profile', 'backend')
        self.assertIn('DRY RUN', preview.stdout)
        self.assertFalse((self.root / 'AGENTS.md').exists())
        applied = self.run_cli('init', self.root, '--profile', 'backend', '--apply')
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertIn('backend', (self.root / '.zero' / 'PROFILE.md').read_text().lower())
        self.assertEqual((self.root / 'CLAUDE.md').read_text(), '@AGENTS.md\n')

    def test_init_never_overwrites_existing_files(self):
        (self.root / 'AGENTS.md').write_text('CUSTOM RULES\n')
        (self.root / 'CLAUDE.md').write_text('CUSTOM CLAUDE\n')
        result = self.run_cli('init', self.root, '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / 'AGENTS.md').read_text(), 'CUSTOM RULES\n')
        self.assertEqual((self.root / 'CLAUDE.md').read_text(), 'CUSTOM CLAUDE\n')
        self.assertTrue((self.root / '.zero' / 'ZERO_RULES.md').exists())

    def test_context_has_budget_and_excludes_secrets(self):
        (self.root / 'service.py').write_text('def useful_symbol():\n    return 123\nJWT_SECRET = useful_symbol\n')
        (self.root / '.env').write_text('useful_symbol=SECRET\n')
        (self.root / 'credentials.py').write_text('useful_symbol=SECRET\n')
        result = self.run_cli('context', self.root, '-q', 'useful_symbol', '--budget-bytes', '200')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('service.py', result.stdout)
        self.assertNotIn('SECRET', result.stdout)
        self.assertNotIn('credentials.py', result.stdout)
        self.assertIn('[potential secret assignment omitted]', result.stdout)

    def test_context_denies_path_traversal(self):
        result = self.run_cli('context', self.root, '-q', 'a', '--scope', '../')
        self.assertEqual(result.returncode, 2)
        self.assertIn('escapes', result.stderr)

    def test_gate_preserves_failure_and_limits_output(self):
        result = self.run_cli('gate', '--output-bytes', '120', self.root, '--',
                              sys.executable, '-c', 'print("X" * 2000); raise SystemExit(7)')
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn('FAIL exit=7', result.stdout)
        self.assertIn('truncated', result.stdout)
        self.assertLess(len(result.stdout), 600)

    def test_gate_success_hides_bulk_logs(self):
        result = self.run_cli('gate', self.root, '--', sys.executable, '-c', 'print("Y" * 3000)')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS exit=0', result.stdout)
        self.assertNotIn('YYYYYY', result.stdout)

    def test_metrics_refuses_to_hide_quality_regression(self):
        report = {'tasks': [{'id': 'task-1',
                             'baseline': {'input_tokens': 100, 'output_tokens': 100, 'success': True},
                             'candidate': {'input_tokens': 30, 'output_tokens': 30, 'success': False}}]}
        file = self.root / 'benchmark.json'
        file.write_text(json.dumps(report))
        result = self.run_cli('metrics', file)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue(json.loads(result.stdout)['quality_regression'])
        self.assertEqual(json.loads(result.stdout)['token_change_pct'], 70)


    def test_init_rejects_symlinked_zero_folder(self):
        outside = self.root / 'outside'
        outside.mkdir()
        project = self.root / 'project'
        project.mkdir()
        (project / '.zero').symlink_to(outside, target_is_directory=True)
        result = self.run_cli('init', project, '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SKIP unsafe path', result.stdout)
        self.assertFalse((outside / 'PROFILE.md').exists())

    def test_metrics_catches_swapped_successes(self):
        report = {'tasks': []}
        for name, before, after in [('a', True, False), ('b', False, True)]:
            report['tasks'].append({
                'id': name,
                'baseline': {'input_tokens': 200, 'output_tokens': 100, 'success': before},
                'candidate': {'input_tokens': 100, 'output_tokens': 50, 'success': after},
            })
        file = self.root / 'swapped.json'; file.write_text(json.dumps(report))
        result = self.run_cli('metrics', file)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['regressed_task_ids'], ['a'])


    def test_relative_document_links(self):
        overlay = CLI.parents[1]
        documents = [overlay / 'ZERO.md', *CLI.parent.rglob('*.md')]
        for document in documents:
            for match in re.finditer(r'\[[^\]]+\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
                link = match.group(1).split('#', 1)[0]
                if not link or '://' in link or link.startswith('mailto:'):
                    continue
                self.assertTrue((document.parent / link).exists(), f'{document}: {link}')

    def test_metrics_rejects_invalid_token_count(self):
        report = {'tasks': [{'id': 'x',
                             'baseline': {'input_tokens': -1, 'output_tokens': 0, 'success': True},
                             'candidate': {'input_tokens': 0, 'output_tokens': 0, 'success': True}}]}
        file = self.root / 'invalid.json'; file.write_text(json.dumps(report))
        result = self.run_cli('metrics', file)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
