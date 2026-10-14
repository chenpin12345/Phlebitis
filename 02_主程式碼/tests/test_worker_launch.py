"""Workers must start from the code folder: since the 01/02/03 split the data root has no `src`."""
import json
import subprocess
import sys
import time
import uuid
from src.paths import CODE_ROOT
from src.workbench import jobs
from test_trash import app  # noqa: F401  (isolated fixture)


def test_worker_starts_in_code_folder(app, monkeypatch):
    c, root, _ = app
    ident = uuid.uuid4().hex
    jobs.folder(ident).mkdir(parents=True)
    with jobs.db() as con:
        con.execute('INSERT INTO jobs(id,idem,kind,state,config,created,updated) VALUES(?,?,?,?,?,?,?)',
                    (ident, ident, 'predict', 'queued', json.dumps({'model': 'yolo11n'}), time.time(), time.time()))
    calls = []

    def fake_popen(args, **kw):
        calls.append((args, kw))
        raise OSError('stop after capturing the launch')
    monkeypatch.setattr(jobs.subprocess, 'Popen', fake_popen)
    jobs.Manager().tick()
    assert calls, 'queued job was not launched'
    args, kw = calls[0]
    assert args[1:3] == ['-m', 'src.workbench.worker']
    assert kw['cwd'] == CODE_ROOT and str(CODE_ROOT) in kw['env']['PYTHONPATH']


def test_worker_module_resolves_from_any_working_directory(tmp_path):
    env = {'PYTHONPATH': str(CODE_ROOT), 'SYSTEMROOT': __import__('os').environ.get('SYSTEMROOT', '')}
    out = subprocess.run([sys.executable, '-c', "import importlib.util as u;print(u.find_spec('src.workbench.worker') is not None)"],
                         cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    assert out.stdout.strip() == 'True', out.stderr
