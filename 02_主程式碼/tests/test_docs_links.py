"""Every relative link in the project's Markdown documents must point to an existing file.

Folders were moved more than once (single folder → 01/02/03 → 04/05); this keeps the
documents a new maintainer reads first from pointing at places that no longer exist.
"""

import re
from pathlib import Path
from urllib.parse import unquote

import pytest

from src import paths

WORKSPACE = paths.WORKSPACE_ROOT
SKIP_DIRS = {'node_modules', '.venv', '.git', '.pytest_cache', '__pycache__', 'dist', 'test-results'}
LINK = re.compile(r'\[[^\]\n]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
FENCE = re.compile(r'^```.*?^```', re.S | re.M)


def documents() -> list[Path]:
    found = []
    for top in ('README.md',):
        if (WORKSPACE / top).is_file():
            found.append(WORKSPACE / top)
    for area in (paths.DOCS_ROOT, paths.CODE_ROOT):
        for path in area.rglob('*.md'):
            if not SKIP_DIRS & set(path.relative_to(area).parts):
                found.append(path)
    # Data, backup and import areas: only their own README files are documents.
    for area in (paths.STORE_ROOT, paths.BACKUP_ROOT, paths.INBOX_ROOT):
        if area == paths.CODE_ROOT or not area.is_dir():
            continue
        for path in area.rglob('README.md'):
            parts = set(path.relative_to(area).parts)
            if not parts & ({'archive', 'runs', 'legacy', 'code_backups'} | SKIP_DIRS):
                found.append(path)
    return sorted(set(found))


def broken_links(path: Path) -> list[str]:
    text = FENCE.sub('', path.read_text(encoding='utf-8'))
    problems = []
    for target in LINK.findall(text):
        if re.match(r'^[a-z]+:', target, re.I) or target.startswith('#'):
            continue  # web links, mailto: and in-page anchors
        relative = unquote(target.split('#', 1)[0])
        if relative and not (path.parent / relative).exists():
            problems.append(target)
    return problems


def test_documents_are_found():
    names = {p.relative_to(WORKSPACE).as_posix() for p in documents()}
    assert 'README.md' in names and any(n.endswith('HANDOVER.md') for n in names)


@pytest.mark.parametrize('path', documents(), ids=lambda p: p.relative_to(WORKSPACE).as_posix())
def test_relative_links_point_to_existing_files(path):
    assert broken_links(path) == []
