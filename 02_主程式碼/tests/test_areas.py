"""Two independent work areas, the authorized 合作醫院 filename rule (v2) and area queries."""
import json
import pytest
from src.common import read_manifest, write_json
from src.data import tasks, filename_rules, source_rules
from src.data.area_migration import migrate_areas
from src.data.dataset import audit, review
from src.imports import external
from test_external_import import env, jpeg  # noqa: F401  (fixture reuse)


def authorize(root):
    cfg = json.loads((root / 'configs/import_sources.json').read_text(encoding='utf-8'))
    cfg['sources']['yida'].update(label_rule='yida_filename_v2', auto_apply=True, authorization={'by': '測試負責人', 'date': '2026-10-14', 'scope': 'test'})
    write_json(root / 'configs/import_sources.json', cfg)


def test_rule_v2_accepts_ll_as_site_and_v1_does_not():
    assert filename_rules.parse('yida_filename_v2', '03/20260104_BED04_LL_2_1.jpg')['value'] == 'stage2'
    assert filename_rules.parse('yida_filename_v1', '03/20260104_BED04_LL_2_1.jpg')['value'] == 'unknown'
    assert filename_rules.parse('yida_filename_v2', 'x/20260104_BED04_XX_2_1.jpg')['value'] == 'unknown'


def test_authorized_import_classifies_without_review_and_keeps_areas_apart(env):
    root, source, files = env
    authorize(root)
    item = external.scan(root, 'yida')
    done = external.commit(root, item['id'], 'k')
    assert done['state'] == 'completed', done.get('error')
    rows = {r['image_id']: r for r in read_manifest(root)}
    by = {e['name']: e.get('image_id') for e in done['items']}
    stage1 = rows[by['08/20260109 BED11_RH_1_1.jpg']]
    assert stage1['cls_review'] == 'confirmed' and stage1['stage_label'] == 'stage1' and stage1['label_state'] == 'positive'
    assert tasks.area_state(stage1, 'det') == 'pending', 'stage photos still need boxes in the YOLO area'
    ll = rows[by['09/20260108 BED10_LL_2_1.jpg']]
    assert ll['stage_label'] == 'stage2', 'LL follows the digit under rule v2'
    legacy = rows['legacy_a']  # 合作醫院 normal photo already in the project (approved negative)
    assert legacy['stage_label'] == 'normal' and tasks.effective(legacy)['detection'] == 'no_target'
    reviews = list((root / 'data/reviews').glob(f"*_{stage1['image_id']}.json"))
    assert reviews and json.loads(reviews[-1].read_text(encoding='utf-8'))['source'] == 'authorized_filename_rule'
    assert not audit(root)['errors']
    # Idempotent: a second run changes nothing.
    again = source_rules.apply_authorized_rules(root)
    assert not any(i.get('cls') == 'applied' or i.get('det') == 'applied' for i in again['items'])


def test_imported_series_share_a_candidate_group(env):
    root, source, files = env
    authorize(root)
    done = external.commit(root, external.scan(root, 'yida')['id'], 'k')
    rows = {r['image_id']: r for r in read_manifest(root)}
    by = {e['name']: e.get('image_id') for e in done['items']}
    first, second = rows[by['08/20260109 BED11_RH_1_1.jpg']], rows[by['09/20260108 BED10_LL_2_1.jpg']]
    assert first['candidate_group'] == 'BED11' and second['candidate_group'] == 'BED10'
    assert first['group_verified'] == 'false', 'a filename code is never a verified patient identity'
    assert rows['legacy_a']['candidate_group'] == 'BED06'
    assert filename_rules.record_code('11/20260111_BED-03_LH_1_1.jpg') == 'BED03', 'hyphen variants merge (safe direction)'
    assert source_rules.assign_candidate_groups(root)['changed'] == 0, 'repeatable'


def test_human_result_is_not_overwritten(env):
    root, source, files = env
    item = external.scan(root, 'yida')
    done = external.commit(root, item['id'], 'k')  # not yet authorized: no auto apply
    target = next(e['image_id'] for e in done['items'] if e['name'] == '08/20260109 BED11_RH_1_1.jpg')
    review(target, task='classification', decision='approve', label='negative', stage='normal', reviewer='醫師', reason='人工判讀為正常', root=root)
    authorize(root)
    report = source_rules.apply_authorized_rules(root)
    entry = next(i for i in report['items'] if i['image_id'] == target)
    assert entry['cls'] in ('conflict_kept_existing', 'human_review_kept')
    row = next(r for r in read_manifest(root) if r['image_id'] == target)
    assert row['stage_label'] == 'normal'


def test_area_migration_is_explicit_and_repeatable(env):
    root, *_ = env
    first = migrate_areas(root)
    row = read_manifest(root)[0]
    assert first['changed'] == 1 and row['cls_review'] == 'confirmed' and row['det_review'] == 'confirmed' and row['detection_state'] == 'no_target'
    assert migrate_areas(root)['changed'] == 0
    assert not audit(root)['errors']


def test_area_query_returns_only_its_own_fields(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from workbench_fixture import configure
    app, _ = configure(tmp_path, monkeypatch)
    with TestClient(app) as c:
        cls = c.get('/api/v1/data-area?area=cls&view=all&size=100').json()
        det = c.get('/api/v1/data-area?area=det&view=all&size=100').json()
        assert cls['counts']['all'] == det['counts']['all'] == 42
        sample = next(i for i in det['items'] if i['image_id'] == 'a_landscape')
        assert set(sample['labels']) == {'detection', 'detection_source', 'usage'} and set(sample['tasks']) == {'detection'}
        sample = next(i for i in cls['items'] if i['image_id'] == 'a_landscape')
        assert 'detection' not in sample['labels'] and 'detection' not in sample['tasks']
        assert c.get('/api/v1/data-area?area=x').status_code == 400
