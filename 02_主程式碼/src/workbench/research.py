"""Explicit promotion and reserved independent-test imports of authorized research assets."""

import json
import shutil
from src.common import ROOT, read_json, write_json, read_manifest, write_manifest, sha256, stamp, inside
from src.workbench.storage import db, audit, file_lock
from src.workbench.lifecycle import asset_path


def promote(case_id, *, independent=False, subject_id=''):
    with db() as con:
        row = con.execute('SELECT data FROM cases WHERE id=?', (case_id,)).fetchone()
        if not row:
            raise ValueError('Unknown case')
        case = json.loads(row[0])
        asset = con.execute('SELECT * FROM assets WHERE id=?', (case['asset'],)).fetchone()
    if not asset or asset['category'] != 'research':
        raise ValueError('Only explicitly authorized research assets may enter datasets')
    if case['state'] != 'confirmed':
        raise ValueError('Human confirmation required')
    source = asset_path(case['asset'])
    hash_value = sha256(source)
    ident = hash_value[:16]
    if independent and not subject_id.strip():
        raise ValueError('Independent test imports require a verified research subject ID')
    with file_lock(ROOT / 'runtime/data.lock'):
        from src.data.dataset import recover_reviews

        recover_reviews(ROOT)
        rows = read_manifest()
        reserved_path = ROOT / 'data/independent_test/manifest.json'
        reserved = read_json(reserved_path) if reserved_path.exists() else []
        if any(r['sha256'] == hash_value for r in rows):
            raise ValueError('This image is already in the review catalog')
        if any(r['sha256'] == hash_value for r in reserved):
            raise ValueError('This image is already reserved for independent testing')
        if not independent and subject_id and any(r['subject_id'] == subject_id for r in reserved):
            raise ValueError('Subject is reserved for independent testing')
        if independent and any(r['subject_id'] == subject_id for r in rows):
            raise ValueError('Subject already occurs in training/review data')
        base = ROOT / ('data/independent_test' if independent else 'data/pending_review/annotation')
        image = base / 'images' / (ident + '.jpg')
        if image.exists():
            raise ValueError('Import destination exists; no files changed')
        image.parent.mkdir(parents=True, exist_ok=True)
        record = {k: '' for k in rows[0]}
        record.update(
            image_id=ident,
            sha256=hash_value,
            image_path=image.relative_to(ROOT).as_posix(),
            status='pending_review',
            label_state=case['label'],
            candidate_group=ident,
            subject_id=subject_id,
            group_verified='true' if subject_id else 'false',
            reviewer=case['reviewer'],
            reason=case.get('notes') or 'authorized research import',
            updated_at=stamp(),
            original_paths=json.dumps(['research_asset:' + case['asset']]),
        )
        manifest = reserved_path if independent else ROOT / 'data/manifest.csv'
        journal = ROOT / 'runtime/review_transactions' / stamp()
        journal.mkdir(parents=True)
        entries = []
        for i, p in enumerate((image, manifest)):
            backup = f'{i}.bak' if p.exists() else None
            if backup:
                shutil.copy2(p, journal / backup)
            entries.append({'path': p.relative_to(ROOT).as_posix(), 'backup': backup})
        tx = {
            'state': 'pending',
            'image_id': ident,
            'files': entries,
            'logs_before': [p.name for p in (ROOT / 'data/reviews').glob('*.json')],
        }
        write_json(journal / 'journal.json', tx)
        try:
            shutil.copy2(source, image)
            if independent:
                record.update(status='independent_test')
                write_json(reserved_path, reserved + [record])
            else:
                write_manifest(rows + [record])
            tx['state'] = 'committed'
            write_json(journal / 'journal.json', tx)
            for p in journal.glob('*.bak'):
                p.unlink()
        except BaseException:
            recover_reviews(ROOT)
            raise
    audit(
        'import_independent_test' if independent else 'promote_case',
        {'case': case_id, 'image_id': ident, 'asset': case['asset']},
    )
    return record
