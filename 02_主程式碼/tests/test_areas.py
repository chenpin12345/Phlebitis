"""Two independent work areas, the authorized 岡山高醫 filename rule (v2) and area queries."""

import json
import pytest
from src.common import read_manifest, write_json
from src.data import tasks, filename_rules, source_rules
from src.data.area_migration import migrate_single_area
from src.data.dataset import audit, review
from src.imports import external
from test_external_import import env, jpeg  # noqa: F401  (fixture reuse)


def authorize(root):
    cfg = json.loads((root / 'configs/import_sources.json').read_text(encoding='utf-8'))
    cfg['sources']['gangshan'].update(
        label_rule='gangshan_filename_v2',
        auto_apply=True,
        authorization={'by': '測試負責人', 'date': '2026-10-14', 'scope': 'test'},
    )
    write_json(root / 'configs/import_sources.json', cfg)


def test_rule_v2_accepts_ll_as_site_and_v1_does_not():
    assert filename_rules.parse('gangshan_filename_v2', '03/20260428_ZZ1401_LL_2_1.jpg')['value'] == 'stage2'
    assert filename_rules.parse('gangshan_filename_v1', '03/20260428_ZZ1401_LL_2_1.jpg')['value'] == 'unknown'
    assert filename_rules.parse('gangshan_filename_v2', 'x/20260428_ZZ1401_XX_2_1.jpg')['value'] == 'unknown'


def test_authorized_import_classifies_without_review(env):
    root, source, files = env
    authorize(root)
    item = external.scan(root, 'gangshan')
    done = external.commit(root, item['id'], 'k')
    assert done['state'] == 'completed', done.get('error')
    rows = {r['image_id']: r for r in read_manifest(root)}
    by = {e['name']: e.get('image_id') for e in done['items']}
    stage1 = rows[by['08/20260519_ZZ0801_RH_1_1.jpg']]
    assert (
        stage1['cls_review'] == 'confirmed'
        and stage1['stage_label'] == 'stage1'
        and stage1['label_state'] == 'positive'
    )
    ll = rows[by['09/20260510_ZZ0101_LL_2_1.jpg']]
    assert ll['stage_label'] == 'stage2', 'LL follows the digit under rule v2'
    legacy = rows['legacy_a']  # 岡山高醫 normal photo already in the project (approved negative)
    assert legacy['stage_label'] == 'normal'
    reviews = list((root / 'data/reviews').glob(f"*_{stage1['image_id']}.json"))
    assert reviews and json.loads(reviews[-1].read_text(encoding='utf-8'))['source'] == 'authorized_filename_rule'
    assert not audit(root)['errors']
    # Idempotent: a second run changes nothing.
    again = source_rules.apply_authorized_rules(root)
    assert not any(i.get('cls') == 'applied' for i in again['items'])


def test_imported_series_share_a_candidate_group(env):
    root, source, files = env
    authorize(root)
    done = external.commit(root, external.scan(root, 'gangshan')['id'], 'k')
    rows = {r['image_id']: r for r in read_manifest(root)}
    by = {e['name']: e.get('image_id') for e in done['items']}
    first, second = rows[by['08/20260519_ZZ0801_RH_1_1.jpg']], rows[by['09/20260510_ZZ0101_LL_2_1.jpg']]
    assert first['candidate_group'] == 'ZZ0801' and second['candidate_group'] == 'ZZ0101'
    assert first['group_verified'] == 'false', 'a filename code is never a verified patient identity'
    assert rows['legacy_a']['candidate_group'] == 'ZZ0601'
    assert (
        filename_rules.record_code('11/20260623_ZZ12-01_LH_1_1.jpg') == 'ZZ1201'
    ), 'hyphen variants merge (safe direction)'
    assert source_rules.assign_candidate_groups(root)['changed'] == 0, 'repeatable'


def test_human_result_is_not_overwritten(env):
    root, source, files = env
    item = external.scan(root, 'gangshan')
    done = external.commit(root, item['id'], 'k')  # not yet authorized: no auto apply
    target = next(e['image_id'] for e in done['items'] if e['name'] == '08/20260519_ZZ0801_RH_1_1.jpg')
    review(
        target,
        decision='approve',
        label='negative',
        stage='normal',
        reviewer='醫師',
        reason='人工判讀為正常',
        root=root,
    )
    authorize(root)
    report = source_rules.apply_authorized_rules(root)
    entry = next(i for i in report['items'] if i['image_id'] == target)
    assert entry['cls'] in ('conflict_kept_existing', 'human_review_kept')
    row = next(r for r in read_manifest(root) if r['image_id'] == target)
    assert row['stage_label'] == 'normal'


def test_single_area_migration_drops_detection_and_keeps_labels(env):
    root, *_ = env
    rows = read_manifest(root)
    rows[0].update(yolo_path='', det_review='confirmed', detection_state='no_target', cls_review='confirmed')
    extra = dict(rows[0], image_id='only_det', sha256='0' * 64, cls_review='excluded', status='approved')
    image = root / 'data/approved/images/only_det.jpg'
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes((root / rows[0]['image_path']).read_bytes())
    box = root / 'data/approved/annotations/only_det.txt'
    box.parent.mkdir(parents=True, exist_ok=True)
    box.write_text('0 0.5 0.5 0.2 0.2')
    extra.update(image_path='data/approved/images/only_det.jpg')
    from src.common import sha256, write_manifest

    extra['sha256'] = '1' * 64
    write_manifest(rows + [extra], root)
    first = migrate_single_area(root)
    after = {r['image_id']: r for r in read_manifest(root)}
    assert first['moved'] == 1
    assert after['only_det']['status'] == 'excluded'
    assert (root / after['only_det']['image_path']).is_file()
    assert (root / 'data/excluded/other/annotations/only_det.txt').is_file(), 'box files stay with the photo'
    assert not {'yolo_path', 'det_review', 'detection_state'} & set(after['only_det'])
    assert after[rows[0]['image_id']]['status'] == rows[0]['status']
    assert migrate_single_area(root)['changed'] == 0


def test_review_history_still_matches_after_the_columns_are_gone():
    old = {'image_id': 'a', 'status': 'approved', 'cls_review': 'confirmed', 'yolo_path': 'x', 'det_review': 'pending'}
    new = {'image_id': 'a', 'status': 'approved', 'cls_review': 'confirmed'}
    assert tasks.row_revision(old) == tasks.row_revision(new)


def test_review_list_has_one_area(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from workbench_fixture import configure

    app, _ = configure(tmp_path, monkeypatch)
    with TestClient(app) as c:
        cls = c.get('/api/v1/data-area?area=cls&view=all&size=100').json()
        assert cls['counts']['all'] == 42
        sample = next(i for i in cls['items'] if i['image_id'] == 'a_landscape')
        assert set(sample['tasks']) == {'binary_classification', 'stage_classification'}
        assert c.get('/api/v1/data-area?area=det').status_code == 400


def test_rule_v3_accepts_rl_and_eleven_digit_prefix_only():
    assert filename_rules.parse('gangshan_filename_v3', '14/2026050901_ZZ0601_RL_1_1.jpg')['value'] == 'stage1'
    assert filename_rules.parse('gangshan_filename_v3', '15/20260509011_ZZ0501_LH_2_1.jpg')['value'] == 'stage2'
    assert (
        filename_rules.parse('gangshan_filename_v2', '14/2026050901_ZZ0601_RL_1_1.jpg')['value'] == 'unknown'
    ), 'older rules unchanged'
    assert filename_rules.parse('gangshan_filename_v2', '15/20260509011_ZZ0501_LH_2_1.jpg')['value'] == 'unknown'
    assert (
        filename_rules.parse('gangshan_filename_v3', 'x/202605090111_ZZ0501_LH_2_1.jpg')['value'] == 'unknown'
    ), 'twelve digits still refused'
    assert filename_rules.parse('gangshan_filename_v3', 'x/20260509_ZZ0501_XX_2_1.jpg')['value'] == 'unknown'
    assert filename_rules.record_code('15/20260509011_ZZ0501_LH_2_1.jpg') == 'ZZ0501'


def test_existing_database_gets_new_upgrades(tmp_path):
    import sqlite3
    from src.workbench import storage
    from src.workbench.migrations import LATEST

    home = tmp_path / 'home'
    with storage.db(home) as con:
        assert con.execute('PRAGMA user_version').fetchone()[0] == LATEST
    # A database from before the detection columns were dropped.
    raw = sqlite3.connect(home / 'workbench.sqlite3')
    raw.execute('ALTER TABLE data_index ADD COLUMN eligible_detection INTEGER NOT NULL DEFAULT 0')
    raw.execute("ALTER TABLE data_index ADD COLUMN det_state TEXT NOT NULL DEFAULT 'pending'")
    raw.execute('CREATE INDEX data_area_det ON data_index(det_state,id)')
    raw.execute('PRAGMA user_version=6')
    raw.commit()
    raw.close()
    with storage.db(home) as con:
        assert con.execute('PRAGMA user_version').fetchone()[0] == LATEST
        columns = {r[1] for r in con.execute('PRAGMA table_info(data_index)')}
    assert not {'eligible_detection', 'det_state'} & columns
