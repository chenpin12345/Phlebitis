"""YOLO and Ultralytics were removed in 2026-11. The word may only stay where old records need it."""

from pathlib import Path

from src import paths

CODE = paths.CODE_ROOT
OLD_WORDS = ('yo' + 'lo', 'ultra' + 'lytics')
SUFFIXES = {'.py', '.ts', '.tsx', '.mjs', '.css', '.ps1', '.json', '.html', '.txt', '.toml', '.bat'}
SKIP_DIRS = {'node_modules', '.venv', '.pytest_cache', '__pycache__', 'dist', 'test-results'}
# What stays, and why: each entry names the file and the only text allowed to carry the word.
ALLOWED = {
    'src/common.py': ("OLD_SNAPSHOT_DIR = 'data/" + 'yo' + "lo'",),  # old snapshots stay where records point
    'src/data/tasks.py': ("'" + 'yo' + "lo_path'",),  # retired manifest column
    'tests/test_areas.py': ('yo' + 'lo_path',),  # migration of that column
    # The old source folder's name, kept in stored provenance strings.
    'tests/test_external_import.py': ('YOLO' + 'Dataset',),
    'src/data/remove_source.py': ('YOLO' + 'Dataset',),
    # Leftover folders of the removed model that the sweep deletes.
    'src/workbench/leftovers.py': ('runtime/ultra' + 'lytics', 'data/yo' + 'lo'),
    'tests/test_rename_source_ids.py': ('data/' + 'yo' + 'lo/',),
    # The original wording of an old authorization record.
    'configs/import_sources.json': ('YO' + 'LO 框選區',),
}
SKIPPED = {'tests/test_no_yolo.py'}


def source_files() -> list[Path]:
    found = []
    for area in ('src', 'scripts', 'configs', 'tests', 'web/src'):
        for path in (CODE / area).rglob('*'):
            if path.is_file() and path.suffix.lower() in SUFFIXES and not SKIP_DIRS & set(path.parts):
                found.append(path)
    found += list((CODE / 'web').glob('*.mjs'))
    found += [CODE / 'requirements.txt', CODE / 'requirements.lock.txt', paths.WORKSPACE_ROOT / '.env.example']
    return found


def test_code_and_screens_do_not_mention_the_removed_model():
    hits = []
    for path in source_files():
        name = path.relative_to(paths.WORKSPACE_ROOT if path.name == '.env.example' else CODE).as_posix()
        if name in SKIPPED:
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
            text = line
            for allowed in ALLOWED.get(name, ()):
                text = text.replace(allowed, '')
            if any(word in text.lower() for word in OLD_WORDS):
                hits.append(f'{name}:{number}')
    assert hits == []


def test_removed_modules_stay_removed():
    for name in (
        'src/model_api.py',
        'src/training',
        'src/data/labels.py',
        'src/workbench/assist.py',
        'configs/train.json',
    ):
        assert not (CODE / name).exists(), name
