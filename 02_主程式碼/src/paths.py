"""Workspace path discovery (pure: no mkdir, no ML imports).

Layout (workspace-layout.json one level above the code folder):
  01_文件與紀錄/        docs, verification evidence, reports   -> DOCS_ROOT
  02_主程式碼/          src, web, tests, scripts, configs       -> CODE_ROOT
  03_模型與影像資料/    data, models, runs, runtime, inbox      -> STORE_ROOT
Without a layout file every root is the code folder (legacy single-folder project).
"""
from __future__ import annotations

import json
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
LAYOUT_FILE = CODE_ROOT.parent / 'workspace-layout.json'
KEYS = ('code', 'storage', 'docs')


def read_layout() -> tuple[Path, dict]:
    if not LAYOUT_FILE.is_file():
        return CODE_ROOT, {}
    root = LAYOUT_FILE.parent.resolve()
    layout = json.loads(LAYOUT_FILE.read_text(encoding='utf-8-sig'))
    if layout.get('version') != 1:
        raise ValueError('Unsupported workspace layout version')
    for key in KEYS:
        value = Path(layout[key])
        if value.is_absolute() or not (root / value).resolve().is_relative_to(root):
            raise ValueError('Layout paths must remain within the workspace: ' + key)
    if (root / layout['code']).resolve() != CODE_ROOT:
        raise ValueError('Layout points to a different code installation')
    return root, layout


WORKSPACE_ROOT, LAYOUT = read_layout()


def _area(key: str) -> Path:
    return (WORKSPACE_ROOT / LAYOUT[key]).resolve() if key in LAYOUT else CODE_ROOT


STORE_ROOT = _area('storage')
DOCS_ROOT = _area('docs')
# Where generated evidence (environment checks, smoke results) is written.
EVIDENCE_DIR = DOCS_ROOT / '驗證報告' if LAYOUT else DOCS_ROOT / 'docs'
LINE_MENU_DIR = DOCS_ROOT / 'LINE選單' if LAYOUT else DOCS_ROOT / 'docs/line_menu'
ENV_FILE = WORKSPACE_ROOT / '.env'
