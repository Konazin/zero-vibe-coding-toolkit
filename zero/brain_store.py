"""Explicit private registry and bounded local Markdown access (no Obsidian API)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES = 256 * 1024
MAX_PROJECTS = 100
META = re.compile(r'^<!-- zero-brain: (.+) -->$')
SECRET = re.compile(r'(?i)(?:api[_-]?key|access[_-]?token|password|secret|authorization)\s*[\"\']?\s*[:=]|-----BEGIN .*PRIVATE KEY-----|\b(?:ghp_|sk-proj-)[A-Za-z0-9_-]+')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_small(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError('Expected a regular, non-symlink file')
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('File exceeds 256 KiB limit')
    return data


def note_path(vault: Path, name: str, markdown=True) -> Path:
    rel = Path(name)
    if rel.is_absolute() or '..' in rel.parts or (markdown and rel.suffix != '.md'):
        raise ValueError('Notes must be relative Markdown paths inside the vault')
    current = vault
    for part in rel.parts:
        if part.startswith('.'):
            raise ValueError('Hidden note paths are forbidden')
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlink note paths are forbidden')
    if not current.resolve().is_relative_to(vault):
        raise ValueError('Note escapes vault')
    return current


def load_registry(value: str):
    config = Path(value).expanduser().resolve()
    data = json.loads(read_small(config))
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('Registry requires version 1')
    if not isinstance(data.get('vault'), str):
        raise ValueError('vault must be an absolute directory path')
    vault = Path(data['vault']).expanduser()
    if not vault.is_absolute() or not vault.is_dir():
        raise ValueError('vault must be an existing absolute directory')
    vault = vault.resolve()
    projects = data.get('projects')
    if not isinstance(projects, dict) or not 1 <= len(projects) <= MAX_PROJECTS:
        raise ValueError('Registry requires 1..100 projects')
    destinations = set()
    for name, item in projects.items():
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name) or not isinstance(item, dict):
            raise ValueError('Invalid project identifier or record')
        if not isinstance(item.get('note'), str):
            raise ValueError('Project requires note')
        target = note_path(vault, item['note'])
        if target in destinations:
            raise ValueError('Projects must have distinct notes')
        destinations.add(target)
        repo = item.get('repo')
        if repo is not None and (not isinstance(repo, str) or not Path(repo).expanduser().is_absolute()):
            raise ValueError('repo must be an explicit absolute path')
    return vault, projects


def project(vault, projects, name):
    if name not in projects:
        raise ValueError('Unknown project; choose an identifier from brain status')
    return note_path(vault, projects[name]['note'])


def note_bytes(path):
    return read_small(path) if path.exists() else b''


def metadata(text):
    lines = text.splitlines()
    match = META.fullmatch(lines[0]) if lines else None
    if not match:
        return {}
    data = json.loads(match[1])
    if not isinstance(data, dict):
        raise ValueError('Invalid note metadata')
    if data.get('updated') is not None:
        if not isinstance(data['updated'], str):
            raise ValueError('Invalid updated timestamp')
        age_days(data['updated'])
    if data.get('sha') is not None and (not isinstance(data['sha'], str) or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', data['sha'])):
        raise ValueError('Invalid source SHA')
    return data


def git_head(item):
    if not item.get('repo'):
        return None
    try:
        result = subprocess.run(
            ['git', '-C', str(Path(item['repo']).expanduser()), 'rev-parse', '--verify', 'HEAD'],
            capture_output=True, text=True, timeout=5,
            env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}, check=False)
        sha = result.stdout.strip()
        return sha if result.returncode == 0 and re.fullmatch(r'[0-9a-f]{40,64}', sha) else None
    except (OSError, subprocess.SubprocessError):
        return None


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def age_days(value):
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return (datetime.now(timezone.utc) - stamp).total_seconds() / 86400


def safe_text(text):
    # Never render control sequences from untrusted notes into a terminal.
    return ''.join(c for c in text if c in '\n\t' or (ord(c) >= 32 and not 127 <= ord(c) <= 159))
