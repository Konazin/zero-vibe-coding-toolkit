"""Three-stage capture. No vault write before explicit hash approval."""
from __future__ import annotations

import difflib
import json
import os
import tempfile
from pathlib import Path

from brain_store import (MAX_BYTES, META, SECRET, digest, git_head, note_bytes,
                         metadata, note_path, project, project_root, read_small,
                         safe_text, utc_now)


def private_path(value, vault):
    path = Path(value).expanduser().absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Private artifact paths cannot contain symlinks')
    path = path.resolve(strict=False)
    if path.is_relative_to(vault):
        raise ValueError('Drafts and backups must stay outside the vault')
    if any((p / '.git').exists() for p in path.parents):
        raise ValueError('Drafts and backups must stay outside Git working trees')
    if not path.parent.is_dir():
        raise ValueError('Create a private draft directory first')
    return path


def write_private(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def encode(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False).encode('utf-8')


def proposed(base, entry, meta, include_metadata=True):
    text = base.decode('utf-8')
    lines = text.splitlines(keepends=True)
    has_metadata = bool(lines and META.fullmatch(lines[0].rstrip('\r\n')))
    if has_metadata:
        text = ''.join(lines[1:])
    addition = text + ('\n\n' if text and not text.endswith('\n\n') else ('\n' if text.endswith('\n') else '')) + entry.strip() + '\n'
    if not has_metadata and not include_metadata:
        return addition.encode('utf-8')
    header = '<!-- zero-brain: ' + json.dumps(meta, sort_keys=True) + ' -->\n'
    return (header + addition).encode('utf-8')


def capture(args, vault, projects):
    target = project(vault, projects, args.project)
    if args.target:
        if not projects[args.project].get('root'):
            raise ValueError('A custom capture target requires an explicitly registered project root')
        target = note_path(vault, args.target)
        root = project_root(vault, projects[args.project]['root'])
        if not target.is_relative_to(root):
            raise ValueError('Capture target must be inside the registered project root')
    draft = private_path(args.draft, vault)
    if not target.parent.is_dir():
        raise ValueError('Note parent directory must already exist; no implicit vault setup')
    base = note_bytes(target)
    if any(not c.isprintable() and c not in '\n\r\t' for c in base.decode('utf-8')):
        raise ValueError('Existing note contains non-printing characters; inspect privately')
    if args.text_file:
        entry = read_small(Path(args.text_file).expanduser()).decode('utf-8')
        if not entry.strip() or SECRET.search(entry) or '<!-- zero-brain:' in entry or any(not c.isprintable() and c not in '\n\r\t' for c in entry):
            raise ValueError('Empty, suspected secret, or reserved metadata in capture input')
        previous = {}
        if base:
            previous = metadata(base.decode('utf-8'))
        reference_sha = previous.get('reference_sha') or previous.get('sha') or projects[args.project].get('reference_sha')
        verified_sha = previous.get('verified_sha')
        modified = utc_now()
        meta = {'captured_at': modified, 'reference_sha': reference_sha,
                'verified_sha': verified_sha, 'updated': modified, 'sha': reference_sha}
        data = {'version': 1, 'project': args.project, 'target': str(target),
                'base_sha256': digest(base), 'base_exists': target.exists(), 'entry': entry,
                'metadata': meta}
        result = proposed(base, entry, data['metadata'], include_metadata=not target.exists() or bool(previous))
        if len(result) > MAX_BYTES or SECRET.search(base.decode('utf-8')):
            raise ValueError('Capture exceeds note limit or existing note contains suspected secrets')
        write_private(draft, encode(data))
        print('DRAFT prepared outside vault. Next: capture PROJECT --draft PATH --review')
        return 0
    data = json.loads(read_small(draft))
    if not isinstance(data, dict) or data.get('version') != 1 or data.get('project') != args.project or data.get('target') != str(target):
        raise ValueError('Draft identity does not match registry/project')
    if data.get('base_sha256') != digest(base) or data.get('base_exists') != target.exists():
        raise ValueError('Note changed since draft preparation; create and review a new draft')
    entry, meta = data.get('entry'), data.get('metadata')
    if not isinstance(entry, str) or not entry.strip() or not isinstance(meta, dict):
        raise ValueError('Invalid draft payload')
    if SECRET.search(entry) or SECRET.search(base.decode('utf-8')) or '<!-- zero-brain:' in entry or any(not c.isprintable() and c not in '\n\r\t' for c in entry):
        raise ValueError('Suspected secrets or reserved metadata; review input privately')
    had_metadata = bool(base and base.decode('utf-8').splitlines() and META.fullmatch(base.decode('utf-8').splitlines()[0]))
    result = proposed(base, entry, meta, include_metadata=not target.exists() or had_metadata)
    if len(result) > MAX_BYTES:
        raise ValueError('Capture exceeds note limit')
    approval = digest(encode(data))
    if args.review:
        print(safe_text(''.join(difflib.unified_diff(base.decode('utf-8').splitlines(True),
              result.decode('utf-8').splitlines(True), fromfile='current', tofile='proposed'))), end='')
        print('REVIEW_SHA256=' + approval)
        print('Review locally. Only explicit user approval authorizes --approve with this hash.')
        return 0
    if args.approve != approval:
        raise ValueError('Approval hash mismatch; review the exact draft first')
    backup = private_path(str(draft) + '.backup', vault)
    # One atomic lock per destination, shared by all drafts targeting this note.
    lock = target.parent / ('.zero-brain-capture-' + digest(str(target).encode()) + '.lock')
    write_private(lock, b'capture\n')
    temporary = None
    try:
        # Recheck after taking the per-note lock; competing approved captures fail explicitly.
        if note_bytes(target) != base or target.exists() != data['base_exists']:
            raise ValueError('Note changed during approval')
        if target.exists():
            write_private(backup, base)  # durable recovery copy; never overwrite a previous backup
            fd, temporary = tempfile.mkstemp(prefix='.zero-brain-', dir=target.parent)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(result)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, target.stat().st_mode & 0o777)
            os.replace(temporary, target)
        else:
            write_private(target, result)
        print('CAPTURED approved note. Existing-note backup, if any: draft path + .backup')
    finally:
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()
        lock.unlink()
    return 0
