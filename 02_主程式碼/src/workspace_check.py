"""Workspace health check for whoever takes over the project.

Used by `python -m src doctor` and by the settings page (環境檢查).  Each item says what was
checked, whether it is fine, and what to do when it is not.  Nothing here changes any file.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from src import paths

AREAS = (
    ('docs', '01 文件與紀錄', paths.DOCS_ROOT),
    ('code', '02 主程式碼', paths.CODE_ROOT),
    ('storage', '03 模型與影像資料', paths.STORE_ROOT),
    ('backups', '04 備份', paths.BACKUP_ROOT),
    ('inbox', '05 匯入區', paths.INBOX_ROOT),
)


def _item(key, name, ok, detail, action=''):
    return {'key': key, 'name': name, 'ok': ok, 'detail': detail, 'action': action if ok is not True else ''}


def _ago(t: float | None) -> str:
    if not t:
        return '從未'
    days = (time.time() - t) / 86400
    return time.strftime('%Y-%m-%d %H:%M', time.localtime(t)) + (f'（{days:.0f} 天前）' if days >= 1 else '（今天）')


def _commit_guard_on() -> bool | None:
    """None when git itself cannot answer; the git item already reports a missing repository."""
    try:
        result = subprocess.run(
            ['git', '-C', str(paths.WORKSPACE_ROOT), 'config', 'core.hooksPath'],
            capture_output=True,
            text=True,
            encoding='utf-8',
        )
    except OSError:
        return None
    return result.stdout.strip().endswith('scripts/githooks')


def check(root: Path | None = None) -> list[dict]:
    from src import common

    root = Path(root) if root else common.ROOT
    items = []
    for key, name, folder in AREAS:
        configured = key in paths.LAYOUT or key == 'code'
        items.append(
            _item(
                'area-' + key,
                name,
                folder.is_dir() and configured,
                str(folder),
                (
                    '檢查根目錄 workspace-layout.json 與資料夾名稱是否一致'
                    if configured
                    else 'workspace-layout.json 缺少這一區'
                ),
            )
        )
    items.append(
        _item(
            'git',
            '版本控制（git）',
            (paths.WORKSPACE_ROOT / '.git').is_dir(),
            '程式與文件的修改紀錄',
            '在工作區根目錄執行 git init，避免改壞程式時無法退回',
        )
    )
    items.append(
        _item(
            'commit-guard',
            '提交防護',
            _commit_guard_on(),
            '擋照片、權重、金鑰、病歷號進 git',
            '執行 setup.bat，或在工作區根目錄執行 git config core.hooksPath 02_主程式碼/scripts/githooks',
        )
    )
    items.append(
        _item(
            'web',
            '網頁已建置',
            common.code_path('web/dist/index.html', root).is_file(),
            'web/dist/index.html',
            '執行根目錄 setup.bat',
        )
    )
    try:
        from src.imports import external

        sources = external.sources(root)
        for key, config in sources.items():
            try:
                base, _ = external.source_base(root, key)
                items.append(_item('source-' + key, '外部來源：' + config.get('name', key), True, str(base)))
            except (OSError, ValueError) as exc:
                items.append(
                    _item(
                        'source-' + key,
                        '外部來源：' + config.get('name', key),
                        False,
                        str(exc),
                        '確認資料夾位置；設定在 02_主程式碼/configs/import_sources.json',
                    )
                )
    except (OSError, ValueError, KeyError) as exc:
        items.append(_item('sources', '外部來源設定', False, str(exc), '檢查 configs/import_sources.json'))
    try:
        from src.workbench import backup, full_backup, settings

        daily = backup.listing(root)
        items.append(
            _item(
                'daily-backup',
                '每日自動備份',
                daily['enabled'] and not daily['due'],
                f"{'開啟' if daily['enabled'] else '關閉'}；上次：{_ago(daily['last_auto'])}；位置：{daily['directory']}",
                (
                    '到設定頁開啟「每天自動備份」，並讓工作台開著'
                    if not daily['enabled']
                    else '開著工作台約 1 分鐘後會自動備份'
                ),
            )
        )
        cfg = settings.load().full_backup
        last = full_backup.load_status().get('last_success')
        due = last is None or time.time() - last > cfg.remind_days * 86400
        items.append(
            _item(
                'full-backup',
                '完整備份（照片與模型）',
                None if not cfg.directory else not due,
                f"位置：{cfg.directory or '尚未設定'}；上次：{_ago(last)}",
                '接上外接硬碟，到設定頁「完整備份」設定位置後按「立即完整備份」',
            )
        )
    except Exception as exc:  # the database may be missing on a fresh copy; report instead of failing
        items.append(_item('backups', '備份狀態', False, str(exc)[:300], '先啟動一次工作台（start.bat）'))
    return items


def summary_lines(items: list[dict]) -> list[str]:
    marks = {True: '正常　', False: '需處理', None: '未設定'}
    lines = []
    for item in items:
        line = f"[{marks[item['ok']]}] {item['name']}：{item['detail']}"
        if item['action']:
            line += f"\n          → {item['action']}"
        lines.append(line)
    return lines
