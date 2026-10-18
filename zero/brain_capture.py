"""Three-stage capture. No vault write before explicit hash approval."""
from __future__ import annotations

import difflib
import json
import os
import tempfile
from pathlib import Path

from brain_store import (MAX_BYTES, META, SECRET, digest, git_head, note_bytes,
                         project, read_small, safe_text, utc_now)


def private_path(value, vault):
    path = Path(value).expanduser().absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Private artifact paths cannot contain symlinks')
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


def proposed(base, entry, meta):
    text = base.decode('utf-8')
    lines = text.splitlines(keepends=True)
    if lines and META.fullmatch(lines[0].rstrip('\r\n')):
        text = ''.join(lines[1:])
    result = '<!-- zero-brain: ' + json.dumps(meta, sort_keys=True) + ' -->\n'
    return (result + text + ('\n\n' if not text.endswith('\n') else '\n') + entry.strip() + '\n').encode('utf-8')


def capture(args, vault, projects):
    target = project(vault, projects, args.project)
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
        data = {'version': 1, 'project': args.project, 'target': str(target),
                'base_sha256': digest(base), 'base_exists': target.exists(), 'entry': entry,
                'metadata': {'updated': utc_now(), 'sha': git_head(projects[args.project])}}
        result = proposed(base, entry, data['metadata'])
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
    result = proposed(base, entry, meta)
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
    lock = private_path(str(draft) + '.lock', vault)
    write_private(lock, b'capture\n')
    temporary = None
    try:
        # Recheck after taking the per-draft lock; never silently rebase approved content.
        if note_bytes(project(vault, projects, args.project)) != base or target.exists() != data['base_exists']:
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
