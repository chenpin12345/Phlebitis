"""One lifecycle authority, shared by readers, submitters and maintenance."""
from contextlib import contextmanager
from functools import wraps
import json
import threading
import time
from src.workbench.storage import file_lock

_local = threading.local()
_mutex = threading.RLock()
TYPES = {'job', 'model', 'audit', 'research_photo', 'legacy_run', 'snapshot'}


@contextmanager
def resource_lock():
    from src.workbench import jobs
    # Reentrant in the same thread, OS-backed across workers/server instances.
    with _mutex:
        if getattr(_local, 'depth', 0):
            _local.depth += 1
            try: yield
            finally: _local.depth -= 1
            return
        started=time.perf_counter()
        deadline = time.monotonic() + 5
        while True:
            guard = file_lock(jobs.JOBS.parent / 'resource-lifecycle.lock')
            try:
                guard.__enter__()
                break
            except RuntimeError:
                if time.monotonic() >= deadline: raise
                time.sleep(.02)
        _local.depth = 1
        from src.telemetry import current
        metrics=current.get()
        if metrics is not None:
            entry=metrics.setdefault('lifecycle_lock',{'ms':0,'calls':0});entry['ms']+=(time.perf_counter()-started)*1000;entry['calls']+=1
        try: yield
        finally:
            _local.depth = 0
            guard.__exit__(None, None, None)


def guarded(fn):
    @wraps(fn)
    def call(*args, **kwargs):
        with resource_lock(): return fn(*args, **kwargs)
    return call


def record(kind, ident):
    from src.workbench import jobs
    if kind not in TYPES: raise ValueError('不支援的資源類型')
    with jobs.db() as con:
        row = con.execute('SELECT * FROM resource_lifecycle WHERE type=? AND id=?', (kind, str(ident))).fetchone()
    if not row: return {'type':kind, 'id':str(ident), 'state':'active', 'revision':0}
    item = dict(row)
    for key in ('summary', 'capacity'):
        item[key] = json.loads(item[key]) if item[key] else None
    return item


def states(kind):
    from src.workbench import jobs
    with jobs.db() as con:
        return {r['id']:r['state'] for r in con.execute('SELECT id,state FROM resource_lifecycle WHERE type=?', (kind,))}


def require_active(kind, ident):
    state = record(kind, ident)['state']
    if state != 'active':
        raise ResourceUnavailable(kind, ident, state)


class ResourceUnavailable(ValueError):
    def __init__(self, kind, ident, state):
        self.kind, self.ident, self.state = kind, str(ident), state
        super().__init__('資源已永久刪除' if state == 'purged' else '資源位於垃圾桶或刪除流程中；請先至垃圾桶查看或還原')


def check_managed_path(path):
    from src.workbench import jobs, registry
    path = path.resolve()
    for kind, root in [('job', jobs.JOBS), ('model', registry.VERSIONS)]:
        if path.is_relative_to(root.resolve()):
            parts = path.relative_to(root.resolve()).parts
            if parts: require_active(kind, parts[0])


def invalidate_capacity(path):
    """Retention takes priority; cached bytes must not survive removed media."""
    from src.workbench import jobs, registry
    path=path.resolve()
    for kind,root in [('job',jobs.JOBS),('model',registry.VERSIONS)]:
        if path.is_relative_to(root.resolve()):
            parts=path.relative_to(root.resolve()).parts
            if parts:
                with jobs.db() as con:
                    con.execute('UPDATE resource_lifecycle SET capacity=NULL WHERE type=? AND id=?',(kind,parts[0]))
