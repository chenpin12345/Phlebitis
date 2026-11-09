"""The one-off rename must change only the name, be reversible, and survive an interruption."""

import importlib.util
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'rename_source_ids.py'
spec = importlib.util.spec_from_file_location('rename_source_ids', SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

OLD, NAME = tool.OLD_ID, tool.OLD_NAME


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='')
    return path


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    review = {
        'after': {'reason': f'{OLD}_filename_v3：保留{NAME}版', 'original_paths': f'["inbox/photos/{OLD}-1/a.jpg"]'}
    }
    write(root, 'data/reviews/a.json', json.dumps(review, ensure_ascii=False, indent=2))
    write(root, 'data/migrations/m.json', json.dumps({'changes': {OLD: 'x', 'before': {OLD: 1}}}))
    write(root, 'data/manifest.csv', f'image_id,reason\r\na,{NAME}\r\nb,clean\r\n')
    write(root, 'data/image_sources.json', json.dumps({'images': {'a': {'aliases': [{'source': OLD}]}}}))
    write(root, 'runtime/imports/receipts/r.json', json.dumps({'batch': OLD, 'source_name': NAME}, ensure_ascii=False))
    write(root, 'data/reviews/clean.json', '{"after": {"reason": "ok"}}')
    write(root, 'data/yolo/snapshot.json', '{"note": "out of scope"}')
    write(root, f'runtime/imports/external/{OLD}-1/14/a.jpg', 'image')
    (root / 'runtime/workbench').mkdir(parents=True)
    con = sqlite3.connect(root / tool.DATABASE)
    con.execute('CREATE TABLE imports(id TEXT, batch TEXT, payload TEXT)')
    con.execute('CREATE TABLE data_index(id TEXT, payload TEXT)')
    con.execute('INSERT INTO imports VALUES (?,?,?)', ('1', OLD, json.dumps({'n': NAME}, ensure_ascii=False)))
    con.execute('INSERT INTO data_index VALUES (?,?)', ('a', f'{OLD}_filename_v3'))
    con.commit()
    con.close()
    return root


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_preview_changes_nothing(project):
    before = files(project)
    found = tool.preview(project)
    assert found['files'] == 5 and found['folders'] == 1
    assert found['database'] == {'imports': 1, 'data_index': 1}
    assert files(project) == before


def test_apply_changes_only_the_name_and_can_be_reversed(project):
    before = files(project)
    assert tool.apply(project) == {'files': 5, 'folders': 1}
    review = json.loads((project / 'data/reviews/a.json').read_text(encoding='utf-8'))
    assert review['after']['reason'] == 'gangshan_filename_v3：保留岡山高醫版'
    assert list(json.loads((project / 'data/migrations/m.json').read_text())['changes']) == ['gangshan', 'before']
    assert (project / 'data/manifest.csv').read_bytes().count(b'\r\n') == 3
    for name, data in before.items():
        if name.endswith(('.sqlite3', '.jpg')):
            continue
        assert tool.restored((project / name).read_bytes()) == data
    assert (project / 'data/reviews/clean.json').read_bytes() == before['data/reviews/clean.json']
    assert (project / 'runtime/imports/external/gangshan-1/14/a.jpg').read_text() == 'image'
    assert not (project / f'runtime/imports/external/{OLD}-1').exists()
    con = sqlite3.connect(project / tool.DATABASE)
    assert con.execute('SELECT batch,payload FROM imports').fetchone() == ('gangshan', '{"n": "岡山高醫"}')
    assert con.execute('SELECT payload FROM data_index').fetchone()[0] == 'gangshan_filename_v3'
    con.close()
    assert tool.preview(project)['files'] == 0 and tool.preview(project)['database'] == {'imports': 0, 'data_index': 0}


def test_apply_keeps_a_copy_of_everything_it_touches(project):
    before = files(project)
    tool.apply(project)
    folder = project / 'backups/修改前副本' / tool.SNAPSHOT_FOLDER
    archive = zipfile.ZipFile(next(folder.glob('records-*.zip')))
    assert archive.read('data/reviews/a.json') == before['data/reviews/a.json']
    assert len(archive.namelist()) == 5
    saved = sqlite3.connect(next(folder.glob('workbench-*.sqlite3')))
    assert saved.execute('SELECT batch FROM imports').fetchone()[0] == OLD
    saved.close()


def test_record_of_the_change_has_no_old_name(project):
    tool.apply(project)
    record = next((project / 'data/migrations').glob('source-name-unify-*.json'))
    assert not tool.has_old(record.read_bytes())
    assert len(json.loads(record.read_text(encoding='utf-8'))['files']) == 5


def test_interrupted_run_finishes_on_the_next_run(project):
    with pytest.raises(RuntimeError, match='測試用中斷'):
        tool.apply(project, fail_after=2)
    assert (project / tool.PROGRESS).exists()
    assert 0 < tool.preview(project)['files'] < 5
    tool.apply(project)
    assert not (project / tool.PROGRESS).exists()
    assert tool.preview(project)['files'] == 0


def test_refuses_a_record_holding_both_names(project):
    write(project, 'data/reviews/b.json', '{"reason": "gangshan ' + OLD + '"}')
    with pytest.raises(RuntimeError, match='同時含新舊名稱'):
        tool.apply(project)
    assert tool.preview(project)['files'] == 6


def test_a_file_with_only_the_new_name_is_left_alone(project):
    path = write(project, 'runtime/imports/watch.json', '{"source": "gangshan"}')
    tool.apply(project)
    assert path.read_text() == '{"source": "gangshan"}'


def test_a_broken_record_stops_before_anything_changes(project):
    write(project, 'data/reviews/broken.json', '{"reason": "' + OLD + '"')

    def records():
        return {k: v for k, v in files(project).items() if k.startswith('data/')}

    before = records()
    with pytest.raises(json.JSONDecodeError):
        tool.apply(project)
    assert records() == before
