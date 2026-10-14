"""Display names and source aliases for project images.

Kept outside the manifest so that a display-name correction is never a label,
image-content or annotation change and does not supersede snapshots.
Only filenames (never full computer paths) are stored for display.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath

from src.common import ROOT, read_json, stamp, write_json

SCHEMA = 1
DISPLAY_RULE = 'source_alias_v1'


def store(root: Path = ROOT) -> Path:
    return root / 'data/image_sources.json'


def load(root: Path = ROOT) -> dict:
    p = store(root)
    return read_json(p) if p.exists() else {'schema_version': SCHEMA, 'images': {}}


def choose(aliases: list[dict]) -> tuple[str | None, bool]:
    """Deterministic display choice: the lexicographically smallest source-relative path.
    Different filenames for the same content are flagged as a conflict."""
    if not aliases:
        return None, False
    ordered = sorted(aliases, key=lambda a: (a['source'], a['relative_path']))
    names = {a['filename'] for a in aliases}
    return ordered[0]['filename'], len(names) > 1


def add_alias(images: dict, image_id: str, alias: dict) -> bool:
    """Add one alias in memory; returns True when it was new."""
    entry = images.setdefault(image_id, {'aliases': []})
    key = (alias['source'], alias['relative_path'], alias['source_sha256'])
    if any((a['source'], a['relative_path'], a['source_sha256']) == key for a in entry['aliases']):
        return False
    rel = PurePosixPath(alias['relative_path'])
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Alias must be relative to its source root')
    entry['aliases'].append({**alias, 'filename': rel.name, 'recorded_at': stamp()})
    name, conflict = choose(entry['aliases'])
    entry.update(display_name=name, display_rule=DISPLAY_RULE, conflict=conflict)
    return True


def save(data: dict, root: Path = ROOT) -> None:
    write_json(store(root), data)


def _names_of(row: dict, entry: dict | None) -> set[str]:
    import json
    import re
    names = set()
    for original in json.loads(row.get('original_paths') or '[]'):
        text = str(original).replace('\\', '/')
        if text.startswith(('research_asset:', 'research_intake:')):
            continue  # provenance tags, not filenames
        names.add(PurePosixPath(text).name)
    stored = PurePosixPath(row.get('image_path', '')).name
    match = re.match(r'^(.*)_[0-9a-f]{16}(\.\w+)$', stored)
    if match:
        names.add(match.group(1) + match.group(2))
    for alias in (entry or {}).get('aliases', []):
        names.add(alias['filename'])
    return {n for n in names if n and not n.startswith(('research_asset:', 'research_intake:'))}


def variants(rows: list[dict], data: dict) -> dict[str, list[str]]:
    """Other images sharing a source filename but with different content. These may be the
    same shot in another encoding: shown as candidates only, never merged automatically."""
    by_name: dict[str, set[str]] = {}
    names = {r['image_id']: _names_of(r, data['images'].get(r['image_id'])) for r in rows}
    for ident, values in names.items():
        for name in values:
            by_name.setdefault(name, set()).add(ident)
    return {ident: sorted({other for n in values for other in by_name[n]} - {ident}) for ident, values in names.items()}


def lookup(image_id: str, data: dict | None = None, root: Path = ROOT) -> dict:
    data = data if data is not None else load(root)
    entry = data['images'].get(image_id)
    if not entry:
        return {'display_name': None, 'aliases': [], 'display_conflict': False}
    return {'display_name': entry.get('display_name'), 'display_conflict': bool(entry.get('conflict')),
            'aliases': [{'source': a['source'], 'relative_path': a['relative_path'], 'filename': a['filename'],
                         'batch': a.get('batch'), 'rule': a.get('label_rule')} for a in entry['aliases']]}
