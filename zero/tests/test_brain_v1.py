"""Zero Brain v1 retrieval and continuity tests use only temporary vaults."""
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / 'zeroctl.py'


class BrainV1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.vault = self.base / 'vault'
        self.vault.mkdir()
        for folder in ('Projects/Alpha/Architecture', 'Projects/Alpha/Decisions',
                       'Projects/Alpha/Sessions', 'Projects/Beta', 'Projects/Gamma'):
            (self.vault / folder).mkdir(parents=True)
        self.note = self.vault / 'Projects/Alpha/Overview.md'
        self.note.write_text('# Alpha overview\nAlpha service uses PostgreSQL for durable transactions.\n', encoding='utf-8')
        self.arch = self.vault / 'Projects/Alpha/Architecture/System-Overview.md'
        self.arch.write_text('# Data architecture\nThe PostgreSQL transaction boundary preserves account consistency.\n', encoding='utf-8')
        self.adr = self.vault / 'Projects/Alpha/Decisions/ADR-0001.md'
        self.adr.write_text('# ADR-0001: PostgreSQL\nStatus: accepted\n\nWe selected PostgreSQL for transactional account consistency.\n', encoding='utf-8')
        self.handoff = self.vault / 'Projects/Alpha/Sessions/Handoff-2026-10-18.md'
        self.handoff.write_text('# Session Handoff\nNext concrete step: add account integration tests.\n', encoding='utf-8')
        (self.vault / 'Projects/Beta/Overview.md').write_text(
            '# Beta overview\nBeta uses Redis for ephemeral rate limiting.\n', encoding='utf-8')
        (self.vault / 'Projects/Beta/Secrets.md').write_text(
            '# Internal\napi_key = "synthetic-test-secret"\nDo not index me.\n', encoding='utf-8')
        self.config = self.base / 'registry.json'
        self.registry = {'version': 1, 'vault': str(self.vault), 'projects': {
            'alpha': {'note': 'Projects/Alpha/Overview.md', 'root': 'Projects/Alpha'},
            'beta': {'note': 'Projects/Beta/Overview.md', 'root': 'Projects/Beta'}}}
        self.save()

    def save(self):
        self.config.write_text(json.dumps(self.registry), encoding='utf-8')

    def cli(self, *args, ok=0):
        result = subprocess.run([sys.executable, str(CLI), 'brain', '--config', str(self.config),
                                 *map(str, args)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, ok, result.stderr + result.stdout)
        return result

    @staticmethod
    def summary(result):
        start = result.stdout.rfind('\n{\n')
        return json.loads(result.stdout[start + 1:] if start >= 0 else result.stdout)

    def test_search_ranks_sources_across_projects_and_scopes_explicitly(self):
        cross = self.cli('search', 'PostgreSQL transaction account', '--budget-tokens', '5000')
        ranked = __import__('re').findall(r'^\[([^\]]+)', cross.stdout, __import__('re').MULTILINE)
        sources = [record.split(' | ')[1].split(':', 1)[0] for record in ranked]
        self.assertIn('Projects/Alpha/Decisions/ADR-0001.md', sources[:3])
        self.assertIn('Projects/Alpha/Architecture/System-Overview.md', sources[:3])
        summary = self.summary(cross)
        self.assertTrue(summary['cross_project'])
        alpha = self.cli('search', 'rate limiting', '--project', 'alpha', '--budget-tokens', '2000')
        self.assertNotIn('Projects/Beta', alpha.stdout)
        architecture = self.cli('search', 'transaction consistency', '--project', 'alpha',
                                '--kind', 'architecture', '--budget-tokens', '2000')
        self.assertIn('Architecture/System-Overview.md', architecture.stdout)
        self.assertNotIn('Decisions/ADR-0001.md', architecture.stdout)
        recent = self.cli('search', 'transaction', '--project', 'alpha', '--after', '2999-01-01',
                          '--budget-tokens', '2000')
        self.assertEqual(self.summary(recent)['matches'], 0)

    def test_search_budget_reports_omissions_and_excludes_secret_documents(self):
        result = self.cli('search', 'postgresql', '--budget-tokens', '10')
        summary = self.summary(result)
        self.assertEqual(summary['output_bytes'], 0)
        self.assertGreater(summary['omitted'], 0)
        index = self.base / 'private-index.json'
        preview = self.cli('index', '--output', index, '--preview')
        self.assertNotIn('synthetic-test-secret', preview.stdout)
        self.assertFalse(index.exists())

    def test_index_requires_stable_explicit_approval_and_is_private(self):
        index = self.base / 'brain-index.json'
        preview = json.loads(self.cli('index', '--output', index, '--preview').stdout)
        self.assertFalse(index.exists())
        self.cli('index', '--output', index, '--approve', preview['sha256'])
        self.assertEqual(stat.S_IMODE(index.stat().st_mode), 0o600)
        content = index.read_text(encoding='utf-8')
        self.assertNotIn('synthetic-test-secret', content)
        self.cli('index', '--output', index, '--approve', preview['sha256'])
        self.assertTrue(index.with_name(index.name + '.backup').exists())
        self.assertEqual(hashlib.sha256(index.read_bytes()).hexdigest(), preview['sha256'])
        search = self.cli('search', 'transaction', '--project', 'alpha', '--index', index,
                          '--budget-tokens', '2000')
        self.assertTrue(self.summary(search)['index_used'])
        self.arch.write_text('# Replaced\nNew content invalidates the index.\n', encoding='utf-8')
        self.cli('search', 'transaction', '--project', 'alpha', '--index', index,
                 '--budget-tokens', '2000', ok=2)

    def test_handoff_and_adr_recovery_are_project_scoped(self):
        latest = self.cli('handoff', 'latest', 'alpha')
        self.assertIn('add account integration tests', latest.stdout)
        self.assertIn('Sessions/Handoff-2026-10-18.md', latest.stdout)
        adrs = json.loads(self.cli('adr', 'list', 'alpha').stdout)
        self.assertEqual(adrs[0]['id'], 'ADR-0001')
        self.assertEqual(adrs[0]['status'], 'accepted')
        self.assertEqual(self.cli('adr', 'list', 'beta').stdout, '[]\n')

    def test_handoff_draft_is_outside_vault_and_never_written_to_note(self):
        draft = self.base / 'private' / 'handoff.md'
        draft.parent.mkdir()
        self.cli('handoff', 'draft', 'alpha', '--objective', 'resume integration tests', '--draft', draft)
        self.assertIn('Next concrete step', draft.read_text(encoding='utf-8'))
        self.assertFalse((self.vault / 'Projects/Alpha/Sessions/Handoff.md').exists())
        self.assertEqual(stat.S_IMODE(draft.stat().st_mode), 0o600)

    def test_dashboard_uses_explicit_preview_approval_and_backup(self):
        preview = self.cli('project', 'dashboard', 'alpha', '--preview')
        self.assertIn('Recent decisions', preview.stdout)
        self.assertFalse((self.vault / 'Projects/Alpha/Dashboard.md').exists())
        summary = json.loads(preview.stdout[preview.stdout.rfind('\n{\n') + 1:])
        self.cli('project', 'dashboard', 'alpha', '--approve', summary['approval_sha256'])
        dashboard = self.vault / 'Projects/Alpha/Dashboard.md'
        self.assertIn('[[Projects/Alpha/Decisions/ADR-0001]]', dashboard.read_text(encoding='utf-8'))
        preview = self.cli('project', 'dashboard', 'alpha', '--preview')
        summary = json.loads(preview.stdout[preview.stdout.rfind('\n{\n') + 1:])
        self.cli('project', 'dashboard', 'alpha', '--approve', summary['approval_sha256'])
        self.assertTrue(dashboard.with_name('Dashboard.md.backup').exists())

    def test_project_registration_requires_preview_hash_and_private_registry(self):
        os.chmod(self.config, 0o600)
        preview = json.loads(self.cli('project', 'add', 'gamma', '--note', 'Projects/Gamma/Overview.md',
                                      '--root', 'Projects/Gamma', '--preview').stdout)
        self.assertNotIn('gamma', json.loads(self.config.read_text())['projects'])
        self.cli('project', 'add', 'gamma', '--note', 'Projects/Gamma/Overview.md', '--root',
                 'Projects/Gamma', '--approve', preview['registry_sha256'])
        self.assertIn('gamma', json.loads(self.config.read_text())['projects'])
        self.assertTrue(self.config.with_name('registry.json.backup').exists())

    def test_init_creates_registry_only_after_approval(self):
        output = self.base / 'new-registry.json'
        preview = subprocess.run([sys.executable, str(CLI), 'brain', 'init', '--vault', self.vault,
                                  '--project', 'alpha', '--note', 'Projects/Alpha/Overview.md',
                                  '--root', 'Projects/Alpha', '--output', output, '--preview'],
                                 capture_output=True, text=True, check=True, timeout=10)
        data = json.loads(preview.stdout)
        self.assertFalse(output.exists())
        subprocess.run([sys.executable, str(CLI), 'brain', 'init', '--vault', self.vault,
                        '--project', 'alpha', '--note', 'Projects/Alpha/Overview.md',
                        '--root', 'Projects/Alpha', '--output', output, '--approve', data['sha256']],
                       capture_output=True, text=True, check=True, timeout=10)
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
        self.assertEqual(json.loads(output.read_text())['projects']['alpha']['root'], 'Projects/Alpha')

    def test_capture_target_must_be_within_registered_root_and_still_approved(self):
        draft = self.base / 'capture.json'
        entry = self.base / 'entry.md'
        entry.write_text('# ADR-0002\nStatus: proposed\n\nUse event logs.\n', encoding='utf-8')
        target = 'Projects/Alpha/Decisions/ADR-0002.md'
        self.cli('capture', 'alpha', '--draft', draft, '--target', target, '--text-file', entry)
        review = self.cli('capture', 'alpha', '--draft', draft, '--target', target, '--review')
        approval = review.stdout.split('REVIEW_SHA256=')[1].splitlines()[0]
        self.cli('capture', 'alpha', '--draft', draft, '--target', target, '--approve', approval)
        self.assertIn('ADR-0002', (self.vault / target).read_text(encoding='utf-8'))
        outside = self.base / 'outside.md'
        outside.write_text('unsafe', encoding='utf-8')
        bad_draft = self.base / 'bad.json'
        self.cli('capture', 'alpha', '--draft', bad_draft, '--target', '../outside.md', '--text-file', entry, ok=2)
        self.assertEqual(outside.read_text(encoding='utf-8'), 'unsafe')

    def test_rejects_symlinked_project_root(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.vault / 'Projects/linked').symlink_to(outside, target_is_directory=True)
        (self.vault / 'Projects/Linked.md').write_text('# Linked\n', encoding='utf-8')
        self.registry['projects']['linked'] = {'note': 'Projects/Linked.md', 'root': 'Projects/linked'}
        self.save()
        self.cli('status', ok=2)  # Registry validation rejects symlink roots before any operation.

    def test_verify_all_documents_reports_broken_links_and_duplicate_passages(self):
        repeated = 'This exact operational guidance is duplicated across project notes for regression coverage.'
        self.arch.write_text(f'# Architecture\n\n{repeated}\n\n[Missing](../No-Such-File.md)\n', encoding='utf-8')
        self.adr.write_text(f'# ADR-0001: PostgreSQL\n\n{repeated}\n', encoding='utf-8')
        report = json.loads(self.cli('verify', '--all-documents', ok=2).stdout)
        self.assertTrue(any(issue['kind'] == 'broken-or-unsafe-link'
                            and issue.get('source_note') == 'Projects/Alpha/Architecture/System-Overview.md'
                            for issue in report['issues']))
        self.assertTrue(any(item['kind'] == 'duplicate-passage' for item in report['notices']))


if __name__ == '__main__':
    unittest.main()
