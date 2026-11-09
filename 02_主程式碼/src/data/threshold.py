"""Decision thresholds chosen inside the training fold (#10).

The threshold is picked from out-of-fold predictions made WITHIN the training members, saved
with the model, and never touched by evaluation: validation photos cannot move it.
"""

from __future__ import annotations

import math

TARGET = 0.90
MIN_THRESHOLD, MAX_THRESHOLD = 1e-6, 1 - 1e-6


def choose(scores, truths, target: float = TARGET) -> dict:
    """The highest threshold that still finds `target` of the positives."""
    positives = sorted((float(s) for s, t in zip(scores, truths) if t == 1), reverse=True)
    negatives = [float(s) for s, t in zip(scores, truths) if t == 0]
    if not positives:
        raise ValueError('沒有陽性照片，不能訂定門檻')
    needed = math.ceil(target * len(positives))
    value = min(max(positives[needed - 1], MIN_THRESHOLD), MAX_THRESHOLD)
    found = sum(s >= value for s in positives)
    return {
        'threshold': value,
        'target_sensitivity': target,
        'inner_sensitivity': found / len(positives),
        'inner_false_positive_rate': sum(s >= value for s in negatives) / len(negatives) if negatives else None,
        'inner_positives': len(positives),
        'inner_negatives': len(negatives),
    }


def inner_folds(truths: list[int], groups: list[str], seed: int, folds: int = 3) -> list[tuple[list[int], list[int]]]:
    """Whole-patient folds inside the training members; every inner training part has both classes."""
    import numpy as np
    from sklearn.model_selection import StratifiedGroupKFold

    per_class = [len({g for g, t in zip(groups, truths) if t == c}) for c in sorted(set(truths))]
    n = min(folds, *per_class) if len(per_class) > 1 else 0
    if n < 2:
        return []
    for attempt in range(20):
        splitter = StratifiedGroupKFold(n_splits=n, shuffle=True, random_state=seed + attempt)
        parts = [(a.tolist(), b.tolist()) for a, b in splitter.split(np.zeros(len(truths)), truths, groups)]
        if all(len({truths[i] for i in train}) == len(per_class) for train, _ in parts):
            return parts
    return []


def from_training(rows: list[dict], truth, scorer, seed: int, target: float = TARGET) -> dict | None:
    """`scorer(fit_rows, held_rows)` returns positive-class scores for held_rows.  `rows` must be
    the training members only.  None when the fold has too few patients for inner predictions."""
    truths = [truth(r) for r in rows]
    parts = inner_folds(truths, [r['group'] for r in rows], seed)
    if not parts:
        return None
    scores = [0.0] * len(rows)
    for train, held in parts:
        values = scorer([rows[i] for i in train], [rows[i] for i in held])
        for i, value in zip(held, values):
            scores[i] = float(value)
    return {
        **choose(scores, truths, target),
        'inner_folds': len(parts),
        'rule': 'inner out-of-fold, training members only',
    }
