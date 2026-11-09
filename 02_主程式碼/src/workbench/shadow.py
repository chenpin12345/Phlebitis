"""Shadow mode for LINE (C2): a candidate model analyses the same photos silently.

The shadow model never produces a message.  Its prediction is computed only after the
patient's reply has been handed to the transport, and only a comparison row is stored
(statuses, classes and scores; no image, no user identifier).  Any shadow failure is
swallowed so it can never change what the patient receives.  The simulator follows the
same rule, so shadow mode can be tried offline.  LINE loads the shadow model at start-up.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

REF = 'shadow.json'


def _ensure(con):
    con.execute(
        '''CREATE TABLE IF NOT EXISTS shadow_predictions(id INTEGER PRIMARY KEY, at REAL, source TEXT, main_artifact TEXT, shadow_artifact TEXT,
        main_status TEXT, shadow_status TEXT, main_class TEXT, shadow_class TEXT, main_score REAL, shadow_score REAL, agree INTEGER, shadow_error TEXT)'''
    )


def current() -> dict | None:
    from src.common import read_json
    from src.workbench import registry

    path = registry.REFS / REF
    value = read_json(path) if path.exists() else None
    return value if value and value.get('artifact') else None


def set_shadow(ident: str | None) -> dict:
    from src.common import read_json, stamp, write_json
    from src.workbench import registry

    path = registry.REFS / REF
    if not ident:
        old = current()
        write_json(path, {'artifact': None, 'stopped': stamp(), 'previous': old})
        return {'artifact': None, 'stopped': True, 'note': 'LINE 下次啟動時不再載入影子模型。'}
    metadata = registry.get(ident)  # integrity, active state
    if metadata.get('extra', {}).get('purpose') == 'checkpoint':
        raise ValueError('Checkpoint 不能作為影子模型')
    line = registry.REFS / 'line.json'
    main = (read_json(line) if line.exists() else None) or {}
    if main.get('artifact') == ident:
        raise ValueError('這個版本已是 LINE 使用中的模型，不需要影子模式')
    value = {'artifact': ident, 'since': stamp(), 'main_at_start': main.get('artifact')}
    write_json(path, value)
    return {**value, 'note': '影子模型只在背景比較，不會回覆病患；LINE 需重新啟動後才會載入。'}


def compare(main: dict, shadow: dict | None, error: str | None = None) -> dict:
    def binary(record):
        return (
            None
            if not record
            else (
                'positive'
                if record.get('status') == 'suspected'
                else 'negative' if record.get('status') == 'not_detected' else record.get('status')
            )
        )

    agree = None if shadow is None else int(binary(main) == binary(shadow))
    return {
        'main_status': main.get('status'),
        'shadow_status': (shadow or {}).get('status'),
        'main_class': main.get('predicted_class'),
        'shadow_class': (shadow or {}).get('predicted_class'),
        'main_score': main.get('prediction_score'),
        'shadow_score': (shadow or {}).get('prediction_score'),
        'agree': agree,
        'shadow_error': error,
    }


def record(
    source: str, main: dict, shadow_artifact: str, shadow: dict | None, error: str | None = None, home=None
) -> None:
    from src.workbench import jobs, storage

    try:
        row = compare(main, shadow, error)
        with storage.db(home) if home else jobs.db() as con:
            _ensure(con)
            con.execute(
                'INSERT INTO shadow_predictions(at,source,main_artifact,shadow_artifact,main_status,shadow_status,main_class,shadow_class,main_score,shadow_score,agree,shadow_error) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                (
                    time.time(),
                    source,
                    main.get('model_version'),
                    shadow_artifact,
                    row['main_status'],
                    row['shadow_status'],
                    row['main_class'],
                    row['shadow_class'],
                    row['main_score'],
                    row['shadow_score'],
                    row['agree'],
                    (error or '')[:300] or None,
                ),
            )
    except Exception:
        pass


def run(predictor, raw: bytes, main: dict, source: str, home=None) -> None:
    """Predict with the shadow model and store the comparison; never raises."""
    if predictor is None:
        return
    ident = getattr(predictor, 'metadata', {}).get('id', '')
    try:
        result, _ = predictor.predict(raw)
        record(source, main, ident, result, home=home)
    except Exception as exc:
        record(source, main, ident, None, type(exc).__name__ + ': ' + str(exc)[:200], home=home)


def stats(period: str = '30', source: str = '') -> dict:
    from src.workbench import jobs

    if period not in ('7', '30', 'all') or source not in ('', 'line', 'simulator'):
        raise ValueError('無效的期間或來源')
    clauses, values = ['1'], []
    if period != 'all':
        clauses.append('at>=?')
        values.append(time.time() - int(period) * 86400)
    if source:
        clauses.append('source=?')
        values.append(source)
    sc = current()
    if sc:
        clauses.append('shadow_artifact=?')
        values.append(sc['artifact'])
    where = ' AND '.join(clauses)
    with jobs.db() as con:
        _ensure(con)
        total, agreed, failed = con.execute(
            f'SELECT COUNT(*),SUM(agree=1),SUM(shadow_error IS NOT NULL) FROM shadow_predictions WHERE {where}', values
        ).fetchone()
        pairs = [
            dict(r)
            for r in con.execute(
                f'SELECT main_status,shadow_status,COUNT(*) n FROM shadow_predictions WHERE {where} GROUP BY 1,2 ORDER BY n DESC',
                values,
            )
        ]
        recent = [
            dict(r)
            for r in con.execute(
                f'SELECT at,source,main_status,shadow_status,main_class,shadow_class,main_score,shadow_score,shadow_error FROM shadow_predictions WHERE {where} AND (agree=0 OR shadow_error IS NOT NULL) ORDER BY at DESC LIMIT 20',
                values,
            )
        ]
    compared = (total or 0) - (failed or 0)
    return {
        'shadow': sc,
        'total': total or 0,
        'compared': compared,
        'agreed': agreed or 0,
        'agreement': (agreed or 0) / compared if compared else None,
        'failed': failed or 0,
        'pairs': pairs,
        'disagreements': recent,
        'period': period,
        'source': source,
    }


def load_predictor(device: str):
    """For the LINE service and the simulator: the shadow predictor, or None."""
    value = current()
    if not value:
        return None
    try:
        from src.workbench.adapters import ModelPredictor

        return ModelPredictor(value['artifact'], device)
    except Exception as exc:
        print('Shadow model not loaded:', type(exc).__name__)
        return None
