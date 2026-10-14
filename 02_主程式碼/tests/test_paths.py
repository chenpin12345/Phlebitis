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
    root, data = layout(tmp_path, monkeypatch, {'version': 1, 'code': '02_主程式碼', 'storage': '03_模型與影像資料', 'docs': '01_文件與紀錄'})
    assert root == tmp_path.resolve() and data['storage'] == '03_模型與影像資料'


@pytest.mark.parametrize('bad', [
    {'version': 2, 'code': '02_主程式碼', 'storage': 's', 'docs': 'd'},
    {'version': 1, 'code': '02_主程式碼', 'storage': '../outside', 'docs': 'd'},
    {'version': 1, 'code': 'other_code', 'storage': 's', 'docs': 'd'},
])
def test_layout_rejects_unsafe_values(tmp_path, monkeypatch, bad):
    with pytest.raises(ValueError):
        layout(tmp_path, monkeypatch, bad)


def test_configs_follow_code_for_real_root_and_stay_local_for_isolated_roots(tmp_path):
    assert common.config_path('service.json', common._STORE) == paths.CODE_ROOT / 'configs/service.json'
    assert common.config_path('service.json', tmp_path) == tmp_path / 'configs/service.json'
    assert common.code_path('web/dist', tmp_path) == tmp_path / 'web/dist'
