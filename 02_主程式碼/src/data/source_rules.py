"""Apply an explicitly authorized filename rule to images from a configured source.

The project owner authorized (2026-10-14) that 合作醫院 photos are classified from their
filenames without per-image review.  Scope, in configs/import_sources.json:
  * other-model (classification) area: binary + stage from the filename rule;
  * YOLO area: filename 'normal' (_0) -> confirmed no lesion (empty label);
    stage 1 / 2 stay pending until the user draws boxes.
Never overwritten: human reviews of the same area, known labels that disagree,
images already containing confirmed boxes, and excluded images.
Each change goes through dataset.review (journal, review log, evidence) and is idempotent.
"""
from __future__ import annotations

from pathlib import Path

from src.common import ROOT, read_json, read_manifest, stamp, write_json
from src.common import config_path
from src.data import filename_rules, sources, tasks

REVIEWER = '依檔名規則（專案負責人授權）'
SOURCE = 'authorized_filename_rule'


def _human_reviews(image_id: str, area: str, root: Path) -> list[dict]:
    items = []
    for path in sorted((root / 'data/reviews').glob(f'*_{image_id}.json')):
        item = read_json(path)
        if item.get('source') == SOURCE or item.get('after', {}).get('reviewer') == 'migration-audit':
            continue
        touched = {'classification': 'cls', 'detection': 'det'}.get(item.get('task'), 'both')
        if touched in (area, 'both'):
            items.append(item)
    return items


def prefill_named_files(root: Path = ROOT, rule: str = 'yida_filename_v2') -> int:
    """Images NOT from the authorized source but carrying the same naming pattern in their
    original filenames get a suggestion only (to confirm in the classification area)."""
    import json
    from pathlib import PurePosixPath
    from src.data import evidence
    names = sources.load(root)['images']
    added = 0
    for row in read_manifest(root):
        if row['image_id'] in names:
            continue
        for original in json.loads(row.get('original_paths') or '[]'):
            text = str(original).replace('\\', '/')
            if text.startswith(('research_asset:', 'research_intake:')):
                continue
            parsed = filename_rules.parse(rule, PurePosixPath(text).name)
            if parsed['value'] == 'unknown':
                continue
            before = len(evidence.read(row['image_id'], root)['entries'])
            evidence.append(row['image_id'], {'task': 'stage_classification', 'value': parsed['value'], 'method': 'rule_prefill', 'source': 'filename_pattern',
                                               'rule_version': rule, 'relative_path': text, 'confirmation': 'pending_human_review',
                                               'note': '非授權來源，只作預填，需人工確認'}, root, dedupe_key=f'{rule}:{row["sha256"]}:{text}')
            added += len(evidence.read(row['image_id'], root)['entries']) > before
    return added


def assign_candidate_groups(root: Path = ROOT) -> dict:
    """Give configured-source images without a group a candidate group from the filename's
    bed/record code, so several photos of the same shot series never split across train and
    validation.  Existing groups are kept; codes equal after removing hyphens reuse the
    existing group name.  Candidate groups stay 'unverified' (group_verified is not changed)."""
    import shutil
    from src.common import write_manifest
    from src.workbench.storage import dataset_lock
    names = sources.load(root)['images']
    config = read_json(config_path('import_sources.json', root))['sources']
    alias_sources = {s.get('alias_source', k) for k, s in config.items()}
    with dataset_lock(root):
        rows = read_manifest(root)
        existing = {}
        for r in rows:
            if r.get('candidate_group'):
                existing.setdefault(r['candidate_group'].replace('-', '').upper(), r['candidate_group'])
        changed = []
        for r in rows:
            if r.get('candidate_group') or r['image_id'] not in names:
                continue
            codes = {filename_rules.record_code(a['relative_path']) for a in names[r['image_id']].get('aliases', []) if a['source'] in alias_sources}
            codes.discard(None)
            if len(codes) != 1:
                continue
            code = codes.pop()
            group = existing.setdefault(code, code)
            r['candidate_group'] = group
            changed.append({'image_id': r['image_id'], 'candidate_group': group})
        if not changed:
            return {'changed': 0}
        backup = root / 'runtime/backups' / f'manifest-before-groups-{stamp()}.csv'
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / 'data/manifest.csv', backup)
        write_manifest(rows, root)
        record = root / 'data/migrations' / f'groups-{stamp()}.json'
        write_json(record, {'schema_version': 1, 'migration': 'candidate_groups_from_filename_code', 'backup': backup.relative_to(root).as_posix(),
                            'note': '候選分組（未核對病患身分），只用於避免同一系列照片跨訓練／驗證', 'changed': changed})
    from src.workbench.queries import data_index
    data_index.invalidate(root)
    return {'changed': len(changed), 'backup': backup.relative_to(root).as_posix(), 'record': record.relative_to(root).as_posix(), 'groups': sorted({c['candidate_group'] for c in changed})}


def apply_authorized_rules(root: Path = ROOT) -> dict:
    from src.data.dataset import review
    groups = assign_candidate_groups(root)
    config = read_json(config_path('import_sources.json', root))['sources']
    names = sources.load(root)['images']
    rows = {r['image_id']: r for r in read_manifest(root)}
    results = []
    for key, source in config.items():
        if not source.get('auto_apply') or not source.get('label_rule'):
            continue
        auth = source.get('authorization', {})
        reason = f"{source['label_rule']}：{auth.get('by', '')} {auth.get('date', '')} 授權依檔名分類，免逐張審核"
        for image_id, entry in sorted(names.items()):
            aliases = [a for a in entry.get('aliases', []) if a['source'] == source.get('alias_source', key)]
            if not aliases or image_id not in rows:
                continue
            parsed = [filename_rules.parse(source['label_rule'], a['relative_path']) for a in aliases]
            values = {p['value'] for p in parsed}
            item = {'image_id': image_id, 'name': aliases[0]['filename'], 'rule': source['label_rule']}
            if len(values) != 1 or 'unknown' in values:
                item.update(cls='skipped', det='skipped', reason='檔名規則無法判定或多個來源檔名不一致：' + '；'.join(r for p in parsed for r in p['reasons']))
                results.append(item)
                continue
            value = values.pop()
            binary = tasks.STAGE_TO_BINARY[value]
            row = rows[image_id]
            e = tasks.effective(row)
            if row['status'] == 'excluded' or e['cls_state'] == 'excluded':
                item['cls'] = 'kept_excluded'
            elif e['binary'] in ('positive', 'negative') and e['binary'] != binary:
                item['cls'] = 'conflict_kept_existing'
            elif _human_reviews(image_id, 'cls', root) and (row.get('stage_label') or '') != value:
                item['cls'] = 'human_review_kept'
            elif e['cls_state'] == 'confirmed' and row.get('stage_label') == value and e['binary'] == binary:
                item['cls'] = 'already'
            else:
                row = review(image_id, task='classification', decision='approve', label=binary, stage=value, reviewer=REVIEWER, reason=reason, source=SOURCE, root=root)
                item['cls'] = 'applied'
            e = tasks.effective(row)
            if value != 'normal':
                item['det'] = 'needs_boxes' if e['det_state'] != 'confirmed' else 'already'
            elif row['status'] == 'excluded' or e['det_state'] == 'excluded':
                item['det'] = 'kept_excluded'
            elif e['detection'] == 'boxes':
                item['det'] = 'conflict_kept_existing'
            elif e['det_state'] == 'confirmed' and e['detection'] == 'no_target':
                item['det'] = 'already'
            elif _human_reviews(image_id, 'det', root):
                item['det'] = 'human_review_kept'
            else:
                row = review(image_id, task='detection', decision='approve', detection='no_target', reviewer=REVIEWER, reason=reason, source=SOURCE, root=root)
                item['det'] = 'applied'
            rows[image_id] = row
            item['value'] = value
            results.append(item)
    summary = {}
    for item in results:
        for area in ('cls', 'det'):
            summary[f"{area}:{item.get(area)}"] = summary.get(f"{area}:{item.get(area)}", 0) + 1
    report = {'schema_version': 1, 'applied_at': stamp(), 'summary': summary, 'items': results, 'candidate_groups': groups}
    if any(i.get('cls') == 'applied' or i.get('det') == 'applied' for i in results):
        write_json(root / 'data/migrations' / f"rules-{report['applied_at']}.json", report)
        from src.workbench.queries import data_index
        data_index.invalidate(root)
        data_index.request_rebuild(root)
    return report
