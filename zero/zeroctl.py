#!/usr/bin/env python3
"""Zero Toolkit: read-first, non-destructive tooling for AI-assisted engineering."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLKIT = Path(__file__).resolve().parent
IGNORED_DIRS = {
    '.git', '.venv', 'venv', 'node_modules', 'dist', 'build', 'coverage',
    '.next', 'target', '.gradle', '.idea', '.zero', 'graphify-out',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.turbo',
}
SKIP_EXT = {'.lock', '.map', '.pem', '.key', '.p12', '.pfx', '.env', '.sqlite', '.db', '.zip', '.jar', '.class'}
SOURCE_EXT = {
    '.py', '.java', '.kt', '.js', '.jsx', '.ts', '.tsx', '.vue', '.go', '.rs',
    '.cs', '.html', '.css', '.scss', '.sql', '.json', '.md', '.yaml', '.yml',
    '.toml', '.xml', '.sh', '.c', '.h', '.cpp', '.hpp', '.gradle', '.properties',
}
SENSITIVE = re.compile(r'(?i)(^\.env($|\.)|secret|credential|password|private[_-]?key|\.pub$|id_rsa|id_ed25519|\.npmrc$|\.pypirc$)')
ASSIGNMENT = re.compile(r'(?i)(api[_-]?key|token|password|secret|authorization)(?:[_-]\w+)?\s*["\']?\s*[:=]\s*')
MAX_SCAN_BYTES = 256 * 1024


def project_root(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f'Not a directory: {value}')
    return path


def stack(root: Path) -> list[str]:
    hints = {
        'package.json': 'Node/Frontend',
        'pyproject.toml': 'Python',
        'requirements.txt': 'Python',
        'pom.xml': 'Java/Maven',
        'build.gradle': 'Java/Gradle',
        'build.gradle.kts': 'Kotlin/Gradle',
        'go.mod': 'Go',
        'Cargo.toml': 'Rust',
        'Dockerfile': 'Container',
    }
    return sorted({label for file, label in hints.items() if (root / file).is_file()})


def doctor(args: argparse.Namespace) -> int:
    root = project_root(args.project)
    data = {
        'project': str(root),
        'stacks': stack(root),
        'agent_files': {p: (root / p).is_file() for p in ('AGENTS.md', 'CLAUDE.md')},
        'optional_tools': {t: bool(shutil.which(t)) for t in ('git', 'rg', 'rtk', 'graphify', 'node', 'python3')},
        'graph_cached': (root / 'graphify-out' / 'graph.json').is_file(),
    }
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print('Project:', data['project'])
        print('Stacks:', ', '.join(data['stacks']) or 'not detected')
        for name, present in data['agent_files'].items():
            print(f'{name}: {"present" if present else "absent"}')
        for name, present in data['optional_tools'].items():
            print(f'{name}: {"available" if present else "not installed"}')
        print('Graphify cached:', data['graph_cached'])
    return 0


def agent_rules(profile: str) -> str:
    return f'''# Zero Engineering Rules

Profile: **{profile}**. Apply `.zero/PROFILE.md` only when relevant to the task.

- Investigate before editing: inspect symbols, contracts, relevant tests, and call sites.
- Search narrowly first; expand context on demand. Do not hide evidence just to save tokens.
- Prefer the smallest coherent change. No speculative abstractions, dependencies, or unrelated refactors.
- Reproduce defects when possible, then add regression checks and run the actual checks.
- Preserve local changes, secrets and provider/authentication settings. Never commit or push without approval.
- Security, accessibility, error handling, data integrity, and migration safety are non-negotiable.
- Use a plan for broad/risky changes, not for trivial repairs. Delegate only truly independent tasks.
- Report commands executed with exit status. Mark unrun tests NOT RUN; never fabricate PASS.
- If output is abbreviated, retain a path to full logs or rerun with full output for failures.
'''


def init(args: argparse.Namespace) -> int:
    root = project_root(args.project)
    profile = (TOOLKIT / 'profiles' / f'{args.profile}.md')
    if not profile.is_file():
        raise ValueError(f'Profile file missing: {profile}')
    rules = agent_rules(args.profile)
    candidates = {
        '.zero/PROFILE.md': profile.read_text(encoding='utf-8'),
        '.zero/ZERO_RULES.md': rules,
        '.zero/QUALITY.md': '''# Quality gate contract\n\nChoose the commands supported by this actual project (lint, typecheck, tests, build, smoke).\nRecord exact commands and run them using the `zeroctl.py` path in the toolkit checkout: `python3 /path/to/toolkit/zero/zeroctl.py gate PROJECT -- COMMAND`.\nA passing gate is required for the touched behavior. Unknown/unconfigured = NOT RUN, not PASS.\n''',
        'AGENTS.md': rules,
        'CLAUDE.md': '@AGENTS.md\n',
    }
    if not args.apply:
        print('DRY RUN (add --apply to write):')
    for relative, content in candidates.items():
        destination = root / relative
        if not destination.parent.resolve().is_relative_to(root) or destination.is_symlink():
            print(f'SKIP unsafe path: {relative}')
            continue
        if destination.exists():
            print(f'SKIP existing: {relative}')
            continue
        print(f'{"CREATE" if args.apply else "WOULD CREATE"}: {relative}')
        if args.apply:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding='utf-8')
    if (root / 'AGENTS.md').exists() and (root / 'AGENTS.md').read_text(encoding='utf-8', errors='replace') != rules:
        print('NOTE: existing AGENTS.md was preserved; manually merge .zero/ZERO_RULES.md.')
    return 0


def source_paths(root: Path):
    """Yield allowed, regular source files. Honor gitignore when Git is available."""
    paths = None
    if shutil.which('git') and (root / '.git').exists():
        try:
            p = subprocess.run(
                ['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=12, check=True,
            )
            paths = [Path(s.decode('utf-8', 'replace')) for s in p.stdout.split(b'\0') if s]
        except (subprocess.SubprocessError, OSError):
            paths = None
    if paths is None:
        paths = []
        for base, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.'))
            for name in sorted(names):
                paths.append((Path(base) / name).relative_to(root))
    for rel in sorted(paths, key=str):
        if any(p in IGNORED_DIRS for p in rel.parts[:-1]):
            continue
        if rel.suffix.lower() not in SOURCE_EXT or rel.suffix.lower() in SKIP_EXT:
            continue
        if SENSITIVE.search(rel.name) or rel.name.startswith('.env'):
            continue
        target = (root / rel).resolve()
        if not target.is_relative_to(root) or not target.is_file() or (root / rel).is_symlink():
            continue
        if target.stat().st_size > MAX_SCAN_BYTES:
            continue
        yield rel, target


def safe_line(line: str) -> str:
    if ASSIGNMENT.search(line):
        return '[potential secret assignment omitted]'
    return line.replace('\x00', '')[:300]


def context(args: argparse.Namespace) -> int:
    root = project_root(args.project)
    scope = (root / args.scope).resolve()
    if not scope.is_relative_to(root):
        raise ValueError('Scope escapes project root')
    if not scope.exists():
        raise ValueError('Scope does not exist')
    term = args.query.casefold()
    if not term:
        raise ValueError('Query cannot be empty')
    used = 0
    hits = 0
    scanned = 0
    limited = False
    for rel, path in source_paths(root):
        if not path.is_relative_to(scope):
            continue
        scanned += 1
        if scanned > args.max_files_scanned:
            limited = True
            break
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except (UnicodeError, OSError):
            continue
        for idx, line in enumerate(lines, 1):
            if term not in line.casefold():
                continue
            record = f'{rel}:{idx}: {safe_line(line)}\n'
            size = len(record.encode('utf-8'))
            if used + size > args.budget_bytes or hits >= args.max_matches:
                limited = True
                break
            print(record, end='')
            used += size
            hits += 1
        if limited:
            break
    print(f'[zero: matches={hits}, scanned_files={min(scanned, args.max_files_scanned)}, output_bytes={used}, truncated={limited}]')
    return 0


def gate(args: argparse.Namespace) -> int:
    root = project_root(args.project)
    command = list(args.command)
    if command and command[0] == '--':
        command.pop(0)
    if not command:
        raise ValueError('Specify command after -- (for example: -- pytest -q)')
    with tempfile.TemporaryFile(mode='w+b') as full_log:
        try:
            result = subprocess.run(command, cwd=root, stdout=full_log, stderr=subprocess.STDOUT, timeout=args.timeout, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
        except OSError as exc:
            print(f'EXEC ERROR: {exc}', file=sys.stderr)
            return 127
        full_log.flush()
        full_log.seek(0, os.SEEK_END)
        size = full_log.tell()
        if args.full or code != 0:
            full_log.seek(0 if args.full else max(0, size - args.output_bytes))
            print(full_log.read().decode('utf-8', 'replace'))
        print(f'[{"PASS" if code == 0 else "FAIL"} exit={code} bytes={size} shown={size if args.full else (min(size,args.output_bytes) if code else 0)}]')
        if code != 0 and not args.full and size > args.output_bytes:
            print('Output was truncated. Rerun with --full to inspect all evidence (may use more tokens).')
        return code if code >= 0 else 128 + (-code)


def metrics(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.file).read_text(encoding='utf-8'))
    tasks = data.get('tasks')
    if not isinstance(tasks, list) or not tasks:
        raise ValueError('Expected non-empty tasks list')
    tally = {'baseline': 0, 'candidate': 0}
    passed = {'baseline': 0, 'candidate': 0}
    seen = set()
    task_regressions = []
    for entry in tasks:
        if not isinstance(entry, dict):
            raise ValueError('Each task must be an object')
        key = entry.get('id')
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError('Task id must be unique and non-empty')
        seen.add(key)
        for side in ('baseline', 'candidate'):
            record = entry.get(side, {})
            if not isinstance(record, dict):
                raise ValueError(f'{key}.{side} must be an object')
            for field in ('input_tokens', 'output_tokens'):
                val = record.get(field)
                if type(val) is not int or val < 0:
                    raise ValueError(f'{key}.{side}.{field} must be a nonnegative integer')
                tally[side] += val
            if type(record.get('success')) is not bool:
                raise ValueError(f'{key}.{side}.success must be boolean')
            passed[side] += int(record['success'])
        if entry['baseline']['success'] and not entry['candidate']['success']:
            task_regressions.append(key)
    saved = (1 - tally['candidate'] / tally['baseline']) * 100 if tally['baseline'] else None
    report = {
        'tasks': len(tasks), 'total_tokens': tally, 'successful_tasks': passed,
        'token_change_pct': round(saved, 2) if saved is not None else None,
        'quality_regression': bool(task_regressions),
        'regressed_task_ids': task_regressions,
        'note': 'Token totals must be provider-reported; compare identical tasks and quality gates. No estimates.',
    }
    print(json.dumps(report, indent=2))
    return 2 if report['quality_regression'] else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Zero Engineering Toolkit (stdlib only)')
    subs = parser.add_subparsers(dest='action', required=True)
    p = subs.add_parser('doctor', help='Inspect project tools and stack; read-only')
    p.add_argument('project'); p.add_argument('--json', action='store_true'); p.set_defaults(fn=doctor)
    p = subs.add_parser('init', help='Preview safe project instruction setup (default dry-run)')
    p.add_argument('project'); p.add_argument('--profile', choices=('frontend', 'backend', 'fullstack'), default='fullstack')
    p.add_argument('--apply', action='store_true'); p.set_defaults(fn=init)
    p = subs.add_parser('context', help='Bounded literal search, no project mutation')
    p.add_argument('project'); p.add_argument('--query', '-q', required=True)
    p.add_argument('--scope', default='.')
    p.add_argument('--budget-bytes', type=int, default=12000)
    p.add_argument('--max-matches', type=int, default=50)
    p.add_argument('--max-files-scanned', type=int, default=3000)
    p.set_defaults(fn=context)
    p = subs.add_parser('gate', help='Run explicit quality command, preserve exit code')
    p.add_argument('project'); p.add_argument('--full', action='store_true')
    p.add_argument('--timeout', type=int, default=300)
    p.add_argument('--output-bytes', type=int, default=16000)
    p.add_argument('command', nargs=argparse.REMAINDER); p.set_defaults(fn=gate)
    p = subs.add_parser('metrics', help='Compare provider-reported token counts and outcomes')
    p.add_argument('file'); p.set_defaults(fn=metrics)
    from brain import register
    register(subs)
    args = parser.parse_args(argv)
    if getattr(args, 'budget_tokens', 1) <= 0:
        parser.error('Token budget must be positive')
    if getattr(args, 'budget_bytes', 1) <= 0 or getattr(args, 'max_matches', 1) <= 0 or getattr(args, 'max_files_scanned', 1) <= 0 or getattr(args, 'output_bytes', 1) <= 0 or getattr(args, 'timeout', 1) <= 0:
        parser.error('Budgets, counts and timeouts must be positive')
    try:
        return args.fn(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
