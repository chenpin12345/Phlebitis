"""Experiment ledger (#17): every planned run and every result, append-only.

`data/experiment_ledger.jsonl` keeps one JSON object per line, chained by hash, so a changed or
removed line is detectable.  It answers "how many settings were tried on this snapshot?", the
number a reader needs to judge the best one.  It holds hashes and metrics only: no photos,
filenames or patient codes.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.common import inside, sha256, stamp
from src.workbench.storage import digest, file_lock

PATH = 'data/experiment_ledger.jsonl'
NOT_THE_PLAN = (
    'dataset',
    'name',
    'cv_group',
    'resume_job',
    'checkpoint_import',
    'device',
    'independent_test',
    'holdout',
)
METRICS = ('sensitivity', 'specificity', 'balanced_accuracy', 'macro_f1', 'accuracy')


def plan_hash(config: dict) -> str:
    return digest({k: v for k, v in config.items() if k not in NOT_THE_PLAN})


def read(root: Path) -> list[dict]:
    path = root / PATH
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def append(root: Path, entry: dict) -> dict:
    path = root / PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(root / 'runtime/experiment-ledger.lock'):
        rows = read(root)
        line = {**entry, 'at': stamp(), 'prev': rows[-1]['hash'] if rows else None}
        line['hash'] = digest(line)
        with path.open('a', encoding='utf-8', newline='\n') as output:
            output.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + '\n')
    return line


def intact(root: Path) -> bool:
    previous = None
    for row in read(root):
        body = {k: v for k, v in row.items() if k != 'hash'}
        if row.get('prev') != previous or digest(body) != row.get('hash'):
            return False
        previous = row['hash']
    return True


def record_run(root: Path, job: str, config: dict) -> None:
    dataset = inside(config['dataset'], root)
    split = dataset.parent / 'split.json'
    append(
        root,
        {
            'event': 'run',
            'job': job,
            'model': config['model'],
            'snapshot': dataset.parent.parent.name,
            'fold': dataset.parent.name,
            'plan_hash': plan_hash(config),
            'split_hash': sha256(split) if split.exists() else None,
            'control': config.get('control') or None,
        },
    )


def record_result(root: Path, report: dict) -> None:
    metrics = report.get('metrics') or {}
    append(
        root,
        {
            'event': 'result',
            'report': report.get('report_id'),
            'artifact': report.get('artifact'),
            'model': report.get('model'),
            'snapshot': report.get('snapshot'),
            'fold': report.get('fold'),
            'purpose': report.get('purpose'),
            'metrics': {k: metrics[k] for k in METRICS if k in metrics},
        },
    )


def summary(root: Path, snapshot: str = '') -> dict:
    rows = [r for r in read(root) if not snapshot or r.get('snapshot') == snapshot]
    runs = [r for r in rows if r['event'] == 'run']
    return {
        'settings': len({r['plan_hash'] for r in runs}),
        'runs': len(runs),
        'results': sum(r['event'] == 'result' for r in rows),
        'intact': intact(root),
    }
