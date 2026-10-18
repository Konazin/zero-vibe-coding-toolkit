"""Brain contracts exercised only with disposable registries, vaults and Git repos."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / 'zeroctl.py'


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        (self.vault / 'Projects').mkdir()
        self.note = self.vault / 'Projects/demo.md'
        self.note.write_text('# Demo\n\n## Decisions\nUse local Markdown.\n', encoding='utf-8')
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--allow-empty', '-qm', 'fixture')
        self.head = self.git('rev-parse', 'HEAD').stdout.strip()
        self.config = self.root / 'registry.json'
        self.registry = {'version': 1, 'vault': str(self.vault),
                         'projects': {'demo': {'note': 'Projects/demo.md', 'repo': str(self.repo)}}}
        self.save_config()
        self.draft = self.root / 'draft.json'
        self.entry = self.root / 'entry.md'
        self.entry.write_text('## Learned\nValidated a fixture.\n', encoding='utf-8')

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def save_config(self):
        self.config.write_text(json.dumps(self.registry), encoding='utf-8')

    def cli(self, *args, ok=0):
        result = subprocess.run([sys.executable, str(CLI), 'brain', '--config', str(self.config),
                                 *map(str, args)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, ok, result.stderr + result.stdout)
        return result

    def stamp(self, updated='2026-01-01T00:00:00+00:00', sha=None):
        meta = {'updated': updated, 'sha': sha or self.head}
        self.note.write_text('<!-- zero-brain: ' + json.dumps(meta) + ' -->\n# Demo\n', encoding='utf-8')

    def prepare(self):
        return self.cli('capture', 'demo', '--draft', self.draft, '--text-file', self.entry)

    def review_hash(self):
        review = self.cli('capture', 'demo', '--draft', self.draft, '--review')
        return review.stdout.split('REVIEW_SHA256=')[1].splitlines()[0]

    def test_read_commands_do_not_write_or_discover_unregistered_notes(self):
        private = self.vault / 'private.md'
        private.write_bytes(b'\xff')
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.cli('status')
        self.cli('recall', 'demo')
        self.cli('switch', 'demo')
        self.cli('verify', ok=2)  # unknown metadata, unrelated invalid UTF-8 is never opened
        after = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_status_unknown_current_stale_and_future(self):
        self.assertEqual(json.loads(self.cli('status').stdout)[0]['sha_state'], 'unknown')
        self.stamp()
        row = json.loads(self.cli('status', '--max-age-days', '0.1').stdout)[0]
        self.assertEqual(row['sha_state'], 'current')
        self.assertEqual(row['date_state'], 'stale')
        self.stamp(updated='2999-01-01T00:00:00Z', sha='a' * 40)
        row = json.loads(self.cli('status').stdout)[0]
        self.assertEqual((row['sha_state'], row['date_state']), ('stale', 'future'))

    def test_status_missing_note_and_unavailable_repo_are_unknown(self):
        self.note.unlink()
        self.registry['projects']['demo']['repo'] = str(self.root / 'missing')
        self.save_config()
        row = json.loads(self.cli('status').stdout)[0]
        self.assertFalse(row['exists'])
        self.assertEqual(row['sha_state'], 'unknown')
        self.cli('recall', 'demo', ok=2)

    def test_recall_budget_query_unicode_and_redaction(self):
        self.note.write_text('match 日本語\nmatch password=hidden-value\n' + 'match data\n' * 100, encoding='utf-8')
        result = self.cli('recall', 'demo', '--query', 'match', '--budget-tokens', '180')
        lines = result.stdout.splitlines(keepends=True)
        summary = json.loads(lines[-1])
        self.assertLessEqual(len(''.join(lines[:-1]).encode()), 180)
        self.assertEqual(summary['output_bytes'], len(''.join(lines[:-1]).encode()))
        self.assertTrue(summary['truncated'])
        self.assertNotIn('hidden-value', result.stdout)
        self.assertIn('日本語', result.stdout)

    def test_tiny_budget_and_invalid_limits(self):
        result = self.cli('recall', 'demo', '--budget-tokens', '1')
        self.assertEqual(json.loads(result.stdout)['output_bytes'], 0)
        self.cli('recall', 'demo', '--budget-tokens', '0', ok=2)
        self.cli('status', '--max-age-days', 'nan', ok=2)
        self.cli('status', '--max-age-days', '-1', ok=2)

    def test_unknown_project(self):
        self.cli('recall', 'other', ok=2)
        self.cli('switch', 'other', ok=2)

    def test_registry_path_traversal_absolute_hidden_and_symlinks(self):
        for note in ('../outside.md', str(self.note), '.hidden.md'):
            with self.subTest(note=note):
                self.registry['projects']['demo']['note'] = note
                self.save_config()
                self.cli('status', ok=2)
        outside = self.root / 'outside'
        outside.mkdir()
        (self.vault / 'linked').symlink_to(outside, target_is_directory=True)
        self.registry['projects']['demo']['note'] = 'linked/note.md'
        self.save_config()
        self.cli('status', ok=2)

    def test_duplicate_notes_and_invalid_registry(self):
        self.registry['projects']['other'] = {'note': 'Projects/demo.md'}
        self.save_config()
        self.cli('status', ok=2)
        self.config.write_text('[]')
        self.cli('status', ok=2)

    def test_capture_prepare_review_approve_preserves_body_and_backup(self):
        before = self.note.read_bytes()
        self.prepare()
        self.assertEqual(self.note.read_bytes(), before)
        self.assertEqual(self.draft.stat().st_mode & 0o777, 0o600)
        approval = self.review_hash()
        self.assertEqual(self.note.read_bytes(), before)
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval)
        self.assertIn(before.decode().strip(), self.note.read_text())
        self.assertIn('Validated a fixture.', self.note.read_text())
        self.assertEqual(Path(str(self.draft) + '.backup').read_bytes(), before)
        self.assertEqual(json.loads(self.cli('status').stdout)[0]['sha_state'], 'current')
        self.cli('verify')
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval, ok=2)

    def test_capture_new_note(self):
        self.note.unlink()
        self.prepare()
        approval = self.review_hash()
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval)
        self.assertTrue(self.note.exists())
        self.assertEqual(self.note.stat().st_mode & 0o777, 0o600)
        self.assertFalse(Path(str(self.draft) + '.backup').exists())

    def test_capture_wrong_hash_and_changed_note_fail_without_write(self):
        self.prepare()
        approval = self.review_hash()
        before = self.note.read_bytes()
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', '0' * 64, ok=2)
        self.assertEqual(self.note.read_bytes(), before)
        self.note.write_text('Human edit\n')
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval, ok=2)
        self.assertEqual(self.note.read_text(), 'Human edit\n')

    def test_tampered_draft_invalidates_approval(self):
        self.prepare()
        approval = self.review_hash()
        data = json.loads(self.draft.read_text())
        data['entry'] = 'Different approved-looking content'
        self.draft.write_text(json.dumps(data))
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval, ok=2)
        self.assertNotIn('Different', self.note.read_text())

    def test_capture_refuses_secret_and_existing_secret(self):
        self.entry.write_text('api_key=not-a-real-key')
        self.cli('capture', 'demo', '--draft', self.draft, '--text-file', self.entry, ok=2)
        self.assertFalse(self.draft.exists())
        self.entry.write_text('A safe entry')
        self.note.write_text('password=not-a-real-password')
        self.cli('capture', 'demo', '--draft', self.draft, '--text-file', self.entry, ok=2)
        self.assertFalse(self.draft.exists())

    def test_capture_refuses_drafts_inside_vault_git_and_symlink(self):
        for draft in (self.vault / 'draft.json', self.repo / 'draft.json'):
            self.cli('capture', 'demo', '--draft', draft, '--text-file', self.entry, ok=2)
            self.assertFalse(draft.exists())
        self.draft.symlink_to(self.entry)
        self.cli('capture', 'demo', '--draft', self.draft, '--text-file', self.entry, ok=2)

    def test_capture_never_overwrites_draft_or_backup(self):
        self.prepare()
        before = self.draft.read_bytes()
        self.cli('capture', 'demo', '--draft', self.draft, '--text-file', self.entry, ok=2)
        self.assertEqual(self.draft.read_bytes(), before)
        approval = self.review_hash()
        backup = Path(str(self.draft) + '.backup')
        backup.write_text('previous recovery copy')
        note_before = self.note.read_bytes()
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval, ok=2)
        self.assertEqual(self.note.read_bytes(), note_before)
        self.assertEqual(backup.read_text(), 'previous recovery copy')

    def test_verify_links_escapes_fences_and_no_repairs(self):
        self.stamp()
        with self.note.open('a') as stream:
            stream.write('\\# literal escaped heading\n[missing](absent.md)\n[[missing-wiki]]\n'
                         '[outside](../../escape.md)\n[web](https://example.invalid)\n'
                         '```md\n[not-a-link](code-example.md)\n```\n')
        before = self.note.read_bytes()
        report = json.loads(self.cli('verify', ok=2).stdout)
        self.assertEqual(len(report['issues']), 4)
        self.assertEqual(report['unchecked_links_or_anchors'], 1)
        self.assertEqual(self.note.read_bytes(), before)

    def test_verify_valid_links_and_stale_source(self):
        self.stamp()
        (self.vault / 'Projects/target.md').write_text('# Target\n')
        with self.note.open('a') as stream:
            stream.write('[target](target.md)\n[[target]]\n')
        self.cli('verify')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--allow-empty', '-qm', 'later')
        report = json.loads(self.cli('verify', ok=2).stdout)
        self.assertIn('stale-source', str(report))

    def test_bad_utf8_oversized_and_malformed_metadata(self):
        for content in (b'\xff', b'x' * (256 * 1024 + 1), b'<!-- zero-brain: [] -->\n'):
            self.note.write_bytes(content)
            self.cli('status', ok=2)
            self.cli('verify', ok=2)

    def test_verify_unclosed_fence_and_control_characters(self):
        self.stamp()
        with self.note.open('a') as stream:
            stream.write('\x00\n```\n')
        report = json.loads(self.cli('verify', ok=2).stdout)
        self.assertIn('control-character', str(report))
        self.assertIn('unclosed-code-fence', str(report))

    def test_invalid_metadata_types_and_registry_paths(self):
        for meta in ({'sha': []}, {'updated': 12}, {'updated': '2026-01-01'}):
            self.note.write_text('<!-- zero-brain: ' + json.dumps(meta) + ' -->\n')
            self.cli('status', ok=2)
            self.cli('verify', ok=2)
        self.registry['vault'] = 12
        self.save_config()
        self.cli('status', ok=2)

    def test_capture_deleted_and_symlinked_destination_invalidates_review(self):
        self.prepare()
        approval = self.review_hash()
        self.note.unlink()
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval, ok=2)
        self.note.symlink_to(self.entry)
        before = self.entry.read_bytes()
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval, ok=2)
        self.assertEqual(self.entry.read_bytes(), before)

    def test_capture_preserves_whitespace_and_rejects_invisible_input(self):
        original = '# Demo  \n\n\n'
        self.note.write_text(original)
        self.prepare()
        approval = self.review_hash()
        self.cli('capture', 'demo', '--draft', self.draft, '--approve', approval)
        self.assertIn(original, self.note.read_text())
        self.entry.write_text('hidden\x1b[2J')
        self.cli('capture', 'demo', '--draft', self.root / 'other.json', '--text-file', self.entry, ok=2)

    def test_verify_parent_relative_links_and_assets(self):
        self.stamp()
        (self.vault / 'asset.png').write_bytes(b'fixture')
        with self.note.open('a') as stream:
            stream.write('[asset](../asset.png)\n')
        self.cli('verify')

    def test_switch_is_explicit_and_stateless(self):
        data = json.loads(self.cli('switch', 'demo').stdout)
        self.assertEqual(data['project'], 'demo')
        self.assertFalse(data['state_written'])
        self.assertFalse((self.vault / '.zero').exists())


if __name__ == '__main__':
    unittest.main()
