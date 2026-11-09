"""Workspace layout: code / storage / docs areas and code-side file routing."""

import json
import pytest
from src import paths, common


def layout(tmp_path, monkeypatch, value):
    code = tmp_path / '02_主程式碼'
    code.mkdir()
    (tmp_path / 'workspace-layout.json').write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    monkeypatch.setattr(paths, 'CODE_ROOT', code.resolve())
    monkeypatch.setattr(paths, 'LAYOUT_FILE', tmp_path / 'workspace-layout.json')
    return paths.read_layout()


def test_layout_resolves_areas(tmp_path, monkeypatch):
    root, data = layout(
        tmp_path,
        monkeypatch,
        {'version': 1, 'code': '02_主程式碼', 'storage': '03_模型與影像資料', 'docs': '01_文件與紀錄'},
    )
    assert root == tmp_path.resolve() and data['storage'] == '03_模型與影像資料'


@pytest.mark.parametrize(
    'bad',
    [
        {'version': 2, 'code': '02_主程式碼', 'storage': 's', 'docs': 'd'},
        {'version': 1, 'code': '02_主程式碼', 'storage': '../outside', 'docs': 'd'},
        {'version': 1, 'code': 'other_code', 'storage': 's', 'docs': 'd'},
    ],
)
def test_layout_rejects_unsafe_values(tmp_path, monkeypatch, bad):
    with pytest.raises(ValueError):
        layout(tmp_path, monkeypatch, bad)


def test_configs_follow_code_for_real_root_and_stay_local_for_isolated_roots(tmp_path):
    assert common.config_path('service.json', common._STORE) == paths.CODE_ROOT / 'configs/service.json'
    assert common.config_path('service.json', tmp_path) == tmp_path / 'configs/service.json'
    assert common.code_path('web/dist', tmp_path) == tmp_path / 'web/dist'


def test_optional_backup_and_inbox_areas_are_validated(tmp_path, monkeypatch):
    base = {'version': 1, 'code': '02_主程式碼', 'storage': '03_模型與影像資料', 'docs': '01_文件與紀錄'}
    for name in ('ok', 'outside', 'absolute'):
        (tmp_path / name).mkdir()
    root, data = layout(tmp_path / 'ok', monkeypatch, {**base, 'backups': '04_備份', 'inbox': '05_匯入區'})
    assert data['backups'] == '04_備份' and data['inbox'] == '05_匯入區'
    with pytest.raises(ValueError):
        layout(tmp_path / 'outside', monkeypatch, {**base, 'backups': '../elsewhere'})
    with pytest.raises(ValueError):
        layout(tmp_path / 'absolute', monkeypatch, {**base, 'inbox': 'C:/elsewhere'})


def test_real_root_uses_04_and_05_while_isolated_roots_stay_local(tmp_path):
    assert common.backup_root(common._STORE) == paths.BACKUP_ROOT
    assert common.inbox_root(common._STORE) == paths.INBOX_ROOT
    assert common.backup_root(tmp_path) == tmp_path / 'backups'
    assert common.inbox_root(tmp_path) == tmp_path / 'inbox'
    assert common.pre_change_dir('manifest', tmp_path) == tmp_path / 'backups/修改前副本/manifest'
    assert common.database_backup(tmp_path, 'x.sqlite3') == tmp_path / 'backups/x.sqlite3'
    real_home = common._STORE / 'runtime/workbench'
    assert common.database_backup(real_home, 'x.sqlite3') == paths.BACKUP_ROOT / '修改前副本/資料庫/x.sqlite3'


def test_record_path_is_relative_to_data_root_or_workspace(tmp_path):
    assert common.record_path(tmp_path / 'data/a.csv', tmp_path) == 'data/a.csv'
    assert common.record_path(paths.WORKSPACE_ROOT / '04_備份/x.csv', tmp_path) == '04_備份/x.csv'
    assert paths.workspace_path('05_匯入區/岡山高醫') == (paths.WORKSPACE_ROOT / '05_匯入區/岡山高醫').resolve()
    assert paths.workspace_path(tmp_path) == tmp_path


def test_workspace_check_lists_every_area_with_a_clear_state(tmp_path, monkeypatch):
    from src import workspace_check
    from src.workbench import jobs, storage

    monkeypatch.setattr(jobs, 'db', lambda: storage.db(tmp_path / 'runtime/workbench'))
    items = workspace_check.check(tmp_path)
    keys = {i['key'] for i in items}
    assert {'area-docs', 'area-code', 'area-storage', 'area-backups', 'area-inbox', 'git', 'web'} <= keys
    assert all(i['ok'] in (True, False, None) and i['name'] and isinstance(i['detail'], str) for i in items)
    assert all(i['action'] for i in items if i['ok'] is False), 'every problem says what to do'
    lines = workspace_check.summary_lines(items)
    assert len(lines) == len(items) and lines[0].startswith('[')
