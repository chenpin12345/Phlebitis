"""The photo source is 岡山高醫. The old name must not come back outside the kept documents."""

from pathlib import Path

from src import paths
from src.imports import external

OLD_WORDS = ('yi' + 'da', '義' + '大')
SUFFIXES = {'.py', '.ts', '.tsx', '.mjs', '.css', '.ps1', '.json', '.md', '.html', '.bat', '.txt'}
SKIP_DIRS = {'node_modules', '.venv', '.git', '.pytest_cache', '__pycache__', 'dist', 'test-results'}
# Kept exactly as written, by decision: research reports, research notes and the slides.
KEPT = (paths.DOCS_ROOT / '研究決策', paths.DOCS_ROOT / '研究筆記', paths.DOCS_ROOT / '簡報')


def project_files() -> list[Path]:
    found = []
    for area in (paths.CODE_ROOT, paths.DOCS_ROOT):
        for path in area.rglob('*'):
            if not path.is_file() or path.suffix.lower() not in SUFFIXES or SKIP_DIRS & set(path.parts):
                continue
            if not any(path.is_relative_to(folder) for folder in KEPT):
                found.append(path)
    found.append(paths.WORKSPACE_ROOT / 'README.md')
    for area in (paths.BACKUP_ROOT, paths.INBOX_ROOT):
        found += [p for p in (area / 'README.md', area / 'photos/README.md', area / 'models/README.md') if p.is_file()]
    return found


def test_old_name_is_gone_from_code_and_documents():
    hits = []
    for path in project_files():
        text = path.read_text(encoding='utf-8', errors='ignore').lower()
        if any(word in text for word in OLD_WORDS):
            hits.append(str(path.relative_to(paths.WORKSPACE_ROOT)))
    assert hits == []


def test_no_file_or_folder_uses_the_old_name():
    hits = []
    for area in (paths.CODE_ROOT, paths.DOCS_ROOT):
        for path in area.rglob('*'):
            if SKIP_DIRS & set(path.parts) or any(path.is_relative_to(folder) for folder in KEPT):
                continue
            if any(word in path.name.lower() for word in OLD_WORDS):
                hits.append(path.name)
    assert hits == []


def test_configured_source_uses_the_new_ids():
    config = external.sources(paths.CODE_ROOT)['gangshan']
    assert config['path'] == '05_匯入區/岡山高醫'
    assert config['alias_source'] == 'gangshan'
    assert config['label_rule'] == 'gangshan_filename_v3'
    assert config['authorization']['date'] == '2026-10-16'
