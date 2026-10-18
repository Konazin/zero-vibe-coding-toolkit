"""Zero Brain v0.2: explicit, local, bounded memory commands."""
from __future__ import annotations

import argparse
import json
import os
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
            reference = meta.get('reference_sha') or meta.get('sha') or item.get('reference_sha')
            verified = item.get('verified_sha') or meta.get('verified_sha')
            modified = None
            if path.exists():
                from datetime import datetime, timezone
                modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
                row['date_source'] = 'filesystem mtime'
            else:
                modified = meta.get('note_modified', meta.get('updated'))
                row['date_source'] = 'metadata fallback' if modified else 'unknown'
            age = age_days(modified) if isinstance(modified, str) else None
            row.update(
                note_modified=modified,
                age_days=round(age, 2) if age is not None else None,
                date_state='unknown' if age is None else ('future' if age < 0 else
                           ('stale' if age > args.max_age_days else 'fresh')),
                reference_sha=reference,
                observed_sha=head,
                reference_state=('matches_head' if head == reference else 'differs_from_head') if head and reference else 'unknown',
                verified_sha=verified,
                verification_state=('verified_at_head' if head == verified else 'verification_stale') if head and verified else 'unverified',
                metadata_state='present' if meta else 'legacy_without_metadata')
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


def _wiki_basename_matches(vault, stem, suffix='.md'):
    matches = []
    seen = 0
    for base, dirs, files in os.walk(vault, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and not (Path(base) / d).is_symlink())
        for filename in files:
            seen += 1
            if seen > 10000:
                return matches, True
            candidate_path = Path(filename)
            if (filename.lower().endswith(suffix.lower())
                    and candidate_path.stem.casefold() == stem.casefold()):
                candidate = Path(base) / filename
                if candidate.is_file() and not candidate.is_symlink():
                    matches.append(candidate.relative_to(vault).as_posix())
                    if len(matches) > 10:
                        return matches, False
    return matches, False



def verify(args, vault, projects):
    issues = []
    unchecked = 0
    notices = []
    for name, item in projects.items():
        path = project(vault, projects, name)
        try:
            if not path.exists():
                raise ValueError('Note is missing')
            text = note_bytes(path).decode('utf-8')
            meta = metadata(text)
            if not meta:
                notices.append({'project': name, 'kind': 'legacy-note-without-zero-brain-metadata'})
            modified = meta.get('captured_at', meta.get('note_modified', meta.get('updated')))
            if modified is not None and age_days(modified) < 0:
                issues.append({'project': name, 'kind': 'future-timestamp'})
            reference = meta.get('reference_sha') or meta.get('sha') or item.get('reference_sha')
            verified = item.get('verified_sha') or meta.get('verified_sha')
            head = git_head(item)
            if reference and head and head != reference:
                issues.append({'project': name, 'kind': 'reference-differs-from-head'})
            if verified and head and head != verified:
                issues.append({'project': name, 'kind': 'verification-stale'})
            if not item.get('repo') and (reference or verified):
                issues.append({'project': name, 'kind': 'source-unavailable'})
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
                markdown_links = re.findall(r'!?\[[^\]]*\]\(([^\s)]+)\)', line)
                wiki_links = re.findall(r'\[\[([^\]]+)\]\]', line)
                for link in markdown_links:
                    parsed = urlsplit(link)
                    if parsed.scheme or parsed.netloc:
                        unchecked += 1
                        continue
                    target = unquote(parsed.path)
                    if not target:
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
                for raw in wiki_links:
                    target = raw.split('|', 1)[0].strip().split('#', 1)[0].split('^', 1)[0].strip()
                    if not target:
                        unchecked += 1
                        continue
                    try:
                        target = unquote(target)
                        has_path = '/' in target or chr(92) in target
                        suffix = Path(target).suffix
                        if has_path:
                            normalized = posixpath.normpath(target.replace(chr(92), '/'))
                            candidate = Path(normalized)
                            if not candidate.suffix:
                                candidate = candidate.with_suffix('.md')
                            resolved = note_path(vault, str(candidate), markdown=False)
                            if not resolved.is_file():
                                raise ValueError('Missing wiki path')
                        else:
                            stem = target[:-len(suffix)] if suffix else target
                            matches, limited = _wiki_basename_matches(vault, stem, suffix or '.md')
                            if limited:
                                issues.append({'project': name, 'line': number, 'kind': 'wikilink-scan-limit', 'target': target})
                            elif len(matches) > 1:
                                issues.append({'project': name, 'line': number, 'kind': 'ambiguous-wikilink',
                                               'target': target, 'matches': matches[:10]})
                            elif not matches:
                                raise ValueError('Missing wikilink')
                    except ValueError:
                        issues.append({'project': name, 'line': number, 'kind': 'broken-or-unsafe-wikilink', 'target': target})
                    if '#' in raw or '^' in raw:
                        unchecked += 1
            if fenced:
                issues.append({'project': name, 'kind': 'unclosed-code-fence'})
        except (ValueError, OSError, UnicodeError, TypeError):
            issues.append({'project': name, 'kind': 'unreadable-or-invalid-note'})
    print(json.dumps({'issues': issues, 'notices': notices, 'unchecked_links_or_anchors': unchecked,
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
