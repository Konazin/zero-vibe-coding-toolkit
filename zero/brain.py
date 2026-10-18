"""Zero Brain v0.2: explicit, local, bounded memory commands."""
from __future__ import annotations

import argparse
import json
import math
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from brain_store import (SECRET, age_days, git_head, load_registry, metadata,
                         note_bytes, note_path, project, safe_text)


def status(args, vault, projects):
    rows = []
    for name, item in projects.items():
        path = project(vault, projects, name)
        row = {'project': name, 'note': item['note'], 'exists': path.is_file()}
        try:
            text = note_bytes(path).decode('utf-8')
            meta = metadata(text)
            head = git_head(item)
            recorded = meta.get('sha')
            sha_state = ('current' if head == recorded else 'stale') if head and recorded else 'unknown'
            updated = meta.get('updated')
            age = age_days(updated) if isinstance(updated, str) else None
            row.update(sha_state=sha_state, head=head, recorded_sha=recorded,
                       age_days=round(age, 2) if age is not None else None,
                       date_state='unknown' if age is None else ('future' if age < 0 else
                                  ('stale' if age > args.max_age_days else 'current')))
        except (ValueError, OSError, UnicodeError, TypeError):
            row['error'] = 'Unreadable note or invalid metadata'
        rows.append(row)
    print(json.dumps(rows, indent=2))
    return 2 if any('error' in row for row in rows) else 0


def recall(args, vault, projects):
    path = project(vault, projects, args.project)
    if not path.exists():
        raise ValueError('Note is missing')
    lines = note_bytes(path).decode('utf-8').splitlines()
    # One UTF-8 byte per estimated token is intentionally conservative; no tokenizer dependency.
    budget = args.budget_tokens
    records = []
    used = 0
    total = 0
    for number, line in enumerate(lines, 1):
        if line.startswith('<!-- zero-brain:') or not line.strip():
            continue
        if args.query and args.query.casefold() not in line.casefold():
            continue
        total += 1
        clean = '[potential secret omitted]' if SECRET.search(line) else safe_text(line)
        record = f'{projects[args.project]["note"]}:{number}: {clean}\n'
        size = len(record.encode('utf-8'))
        if used + size <= budget:
            records.append(record)
            used += size
    print(''.join(records), end='')
    print(json.dumps({'output_bytes': used, 'estimated_tokens_upper_bound': used,
                      'budget_tokens': budget, 'matches': len(records),
                      'truncated': len(records) < total, 'tokenizer': 'UTF-8 bytes; estimate only'}))
    return 0


def switch(args, vault, projects):
    project(vault, projects, args.project)
    # Deliberately stateless: every later invocation still requires config/project.
    print(json.dumps({'project': args.project, 'note': projects[args.project]['note'],
                      'repo': projects[args.project].get('repo'), 'state_written': False,
                      'instruction': 'Recall this project explicitly; verify claims against Git and tests.'}, indent=2))
    return 0


def verify(args, vault, projects):
    issues = []
    unchecked = 0
    for name, item in projects.items():
        path = project(vault, projects, name)
        try:
            if not path.exists():
                raise ValueError('Note is missing')
            text = note_bytes(path).decode('utf-8')
            meta = metadata(text)
            if not meta.get('updated') or not meta.get('sha'):
                issues.append({'project': name, 'kind': 'unknown-source-metadata'})
            else:
                if age_days(meta['updated']) < 0:
                    issues.append({'project': name, 'kind': 'future-timestamp'})
                if not re.fullmatch(r'[0-9a-f]{40,64}', meta['sha']):
                    raise ValueError('Invalid source SHA')
                head = git_head(item)
                if not head:
                    issues.append({'project': name, 'kind': 'source-unavailable'})
                elif head != meta['sha']:
                    issues.append({'project': name, 'kind': 'stale-source'})
            if '\x00' in text or any(ord(c) < 32 and c not in '\n\r\t' for c in text):
                issues.append({'project': name, 'kind': 'control-character'})
            fenced = False
            marker = ''
            for number, line in enumerate(text.splitlines(), 1):
                fence = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
                if fence:
                    if not fenced:
                        fenced, marker = True, fence[1]
                    elif fence[1][0] == marker[0] and len(fence[1]) >= len(marker):
                        fenced = False
                    continue
                if fenced:
                    continue
                if re.match(r'^\\[#>|-]', line):
                    issues.append({'project': name, 'line': number, 'kind': 'suspected-escaped-markdown'})
                links = re.findall(r'!?\[[^\]]*\]\(([^\s)]+)\)', line)
                links += [s.split('|')[0] for s in re.findall(r'\[\[([^\]]+)\]\]', line)]
                for link in links:
                    parsed = urlsplit(link)
                    if parsed.scheme or parsed.netloc:
                        unchecked += 1
                        continue
                    target = unquote(parsed.path)
                    if not target:  # anchors are not resolved by this lightweight checker
                        unchecked += 1
                        continue
                    try:
                        relative = Path(posixpath.normpath(str(path.parent.relative_to(vault) / target)))
                        if not relative.suffix:
                            relative = relative.with_suffix('.md')
                        dest = note_path(vault, str(relative), markdown=False)
                        if not dest.is_file():
                            raise ValueError('Missing link')
                    except ValueError:
                        issues.append({'project': name, 'line': number, 'kind': 'broken-or-unsafe-link'})
                    if parsed.fragment:
                        unchecked += 1
            if fenced:
                issues.append({'project': name, 'kind': 'unclosed-code-fence'})
        except (ValueError, OSError, UnicodeError, TypeError):
            issues.append({'project': name, 'kind': 'unreadable-or-invalid-note'})
    print(json.dumps({'issues': issues, 'unchecked_links_or_anchors': unchecked,
                      'scope': 'Registered notes only; no network, no Markdown repair, no source truth proof.'}, indent=2))
    return 2 if issues else 0


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('Must be positive and finite')
    return number


def run(args):
    vault, projects = load_registry(args.config)
    if args.brain_action == 'capture':
        from brain_capture import capture
        return capture(args, vault, projects)
    return {'status': status, 'recall': recall, 'switch': switch, 'verify': verify}[args.brain_action](args, vault, projects)


def register(subs):
    parser = subs.add_parser('brain', help='Opt-in local Markdown memory; explicit private registry')
    parser.add_argument('--config', required=True, help='Private registry JSON (never discovered automatically)')
    actions = parser.add_subparsers(dest='brain_action', required=True)
    p = actions.add_parser('status', help='Read freshness by metadata date and local Git SHA')
    p.add_argument('--max-age-days', type=positive, default=7)
    p = actions.add_parser('recall', help='Bounded project note retrieval')
    p.add_argument('project'); p.add_argument('--query', default='')
    p.add_argument('--budget-tokens', type=int, default=2000)
    p = actions.add_parser('switch', help='Emit explicit context without persisting active state')
    p.add_argument('project')
    actions.add_parser('verify', help='Check registered notes and local Markdown references; never repair')
    p = actions.add_parser('capture', help='Prepare, review, then explicitly approve an append')
    p.add_argument('project'); p.add_argument('--draft', required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--text-file'); mode.add_argument('--review', action='store_true')
    mode.add_argument('--approve', metavar='REVIEW_SHA256')
    parser.set_defaults(fn=run)
