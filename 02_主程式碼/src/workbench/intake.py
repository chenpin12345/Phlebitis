"""LINE research intake.

Analysis and research use are separate.  A photo becomes a research photo only after
an explicit, versioned consent event (a signed LINE postback, or a clearly marked
simulator event).  Research photos are clean copies (EXIF stripped, no boxes or text).
Model output is stored as reference only and never becomes a label.  Promotion to
data review is an explicit human action.  Withdrawal stops use immediately through
``usage_revocations``; physical cleanup is a retryable background task.
Retention is "until withdrawal" (no automatic expiry), as decided by the project owner.
"""
from __future__ import annotations

import io
import json
import shutil
import time
import uuid
from pathlib import Path

from PIL import Image

from src.common import ROOT, inside, read_json, read_manifest, sha256, stamp, write_json, write_manifest
from src.common import config_path
from src.workbench.storage import HOME, audit, db

STATES = ('received', 'reviewed', 'needs_changes', 'rejected', 'promoted', 'withdrawn')
SOURCES = ('line', 'simulator')


def consent_config(root: Path | None = None) -> dict:
    data = read_json(config_path('research_consent.json', _root(root)))
    if data.get('schema_version') != 1 or data.get('current_version') not in data.get('versions', {}):
        raise ValueError('研究同意設定無效')
    return data


def offer(source: str, root: Path | None = None) -> dict | None:
    """The consent request to show after an analysis, or None when not enabled for this source."""
    try:
        cfg = consent_config(root)
    except (OSError, ValueError):
        return None
    current = cfg['versions'][cfg['current_version']]
    if source == 'line' and not (cfg.get('line_enabled') and current.get('approved')):
        return None
    if source == 'simulator' and not cfg.get('simulator_enabled'):
        return None
    return {'version': cfg['current_version'], 'title': current['title'], 'text': current['text'], 'scope': current['scope'],
            'retention': current.get('retention'), 'approved': bool(current.get('approved'))}


def save_pending(raw: bytes, path: Path, config: dict) -> None:
    """Clean original kept only for the result lifetime so the user can decide on consent."""
    from src.inference.engine import decode_image
    image = decode_image(raw, config)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    image.save(tmp, format='JPEG', quality=95)
    tmp.replace(path)


def _home(home):
    return Path(home) if home else HOME


def _root(root):
    return Path(root) if root else ROOT


def decide(*, source, simulated, user_key, session, event_id, message_id, result_token, version, decision, pending, prediction, home=None, root=None, clock=time.time) -> dict:
    """Record one consent decision. Idempotent per webhook event; one active consent per message."""
    if source not in SOURCES or decision not in ('accept', 'decline'):
        raise ValueError('Invalid consent decision')
    expected = offer(source, root)
    if expected is None:
        return {'status': 'disabled'}
    if version != expected['version']:
        return {'status': 'version_mismatch'}
    now = clock()
    ident = uuid.uuid4().hex
    with db(_home(home)) as con:
        con.execute('BEGIN IMMEDIATE')
        if con.execute('SELECT 1 FROM research_consents WHERE event_id=?', (event_id,)).fetchone():
            return {'status': 'duplicate'}
        active = con.execute("SELECT id FROM research_consents WHERE source=? AND message_id=? AND decision='accept' AND withdrawn_at IS NULL", (source, message_id)).fetchone()
        if decision == 'accept' and active:
            return {'status': 'already', 'consent': active[0]}
        if decision == 'accept' and (pending is None or not Path(pending).is_file()):
            return {'status': 'expired'}
        detail = {'consent_text_version': version, 'approved_version': expected['approved'], 'simulated': bool(simulated)}
        con.execute('INSERT INTO research_consents(id,source,simulated,user_key,session,event_id,message_id,result_token,version,scope,decision,decided_at,detail) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (ident, source, int(bool(simulated)), user_key, session, event_id, message_id, result_token, version, expected['scope'], decision, now, json.dumps(detail, ensure_ascii=False)))
        intake = None
        if decision == 'accept':
            intake = uuid.uuid4().hex
            folder = _home(home) / 'research_intake' / intake
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / 'original.jpg'
            shutil.copyfile(pending, target)
            with Image.open(target) as im:
                im.verify()
            con.execute('INSERT INTO research_intake(id,consent_id,asset_path,image_sha256,source,simulated,received_at,state,prediction,usage_state,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                        (intake, ident, f'research_intake/{intake}/original.jpg', sha256(target), source, int(bool(simulated)), now, 'received',
                         json.dumps(prediction, ensure_ascii=False) if prediction else None, 'test_only' if simulated else 'active', now))
    audit('research_consent', {'consent': ident, 'decision': decision, 'source': source, 'simulated': bool(simulated), 'intake': intake, 'version': version}, home=_home(home))
    return {'status': 'recorded', 'consent': ident, 'intake': intake}


def _revoke(con, row, reason, source_label, now):
    """Inside a transaction: stop all research use of one intake item immediately."""
    con.execute("UPDATE research_intake SET usage_state='withdrawn',state='withdrawn',cleanup_state='pending',revision=revision+1,updated=? WHERE id=?", (now, row['id']))
    con.execute("UPDATE research_consents SET withdrawn_at=COALESCE(withdrawn_at,?) WHERE id=?", (now, row['consent_id']))
    for kind, value in (('intake', row['id']), ('consent', row['consent_id']), ('sha256', row['image_sha256']), ('image', row['promoted_image_id'])):
        if value:
            con.execute('INSERT OR IGNORE INTO usage_revocations(kind,ident,at,reason,source) VALUES(?,?,?,?,?)', (kind, value, now, reason, source_label))
    con.execute('INSERT OR IGNORE INTO cleanup_tasks(id,kind,target,state,created,updated,detail) VALUES(?,?,?,?,?,?,?)',
                ('withdraw:' + row['id'], 'research_withdrawal', row['id'], 'pending', now, now, json.dumps({'reason': reason, 'promoted_image_id': row['promoted_image_id']}, ensure_ascii=False)))


def withdraw_user(*, source, user_key, event_id, reason='使用者撤回研究同意', home=None, clock=time.time) -> dict:
    """User-initiated withdrawal (LINE text command). Never waits for GPU, dataset or cleanup locks."""
    now = clock()
    with db(_home(home)) as con:
        con.execute('BEGIN IMMEDIATE')
        rows = con.execute("SELECT i.* FROM research_intake i JOIN research_consents c ON c.id=i.consent_id WHERE c.source=? AND c.user_key=? AND c.decision='accept' AND c.withdrawn_at IS NULL", (source, user_key)).fetchall()
        for row in rows:
            _revoke(con, row, reason, f'{source}:{event_id}', now)
        con.execute("UPDATE research_consents SET withdrawn_at=COALESCE(withdrawn_at,?),withdraw_event=COALESCE(withdraw_event,?) WHERE source=? AND user_key=? AND decision='accept'", (now, event_id, source, user_key))
    if rows:
        audit('research_withdrawal', {'source': source, 'count': len(rows), 'event': event_id}, home=_home(home))
        _refresh_index()
    return {'withdrawn': len(rows)}


def withdraw_intake(ident, *, reason, actor, home=None, clock=time.time) -> dict:
    """Workbench-initiated withdrawal (e.g. the participant asked by another channel)."""
    if not reason.strip():
        raise ValueError('撤回需要記錄原因')
    now = clock()
    with db(_home(home)) as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT * FROM research_intake WHERE id=?', (ident,)).fetchone()
        if not row:
            raise FileNotFoundError(ident)
        if row['usage_state'] == 'withdrawn':
            return dict(row)
        _revoke(con, row, reason, 'workbench:' + (actor or 'unrecorded'), now)
        row = con.execute('SELECT * FROM research_intake WHERE id=?', (ident,)).fetchone()
    audit('research_withdrawal', {'intake': ident, 'reason': reason}, home=_home(home), actor=actor)
    _refresh_index()
    return public(dict(row))


def _refresh_index():
    try:
        from src.workbench.queries import data_index
        data_index.invalidate(_root(None))
        data_index.request_rebuild(_root(None))
    except Exception:
        pass  # Query-time revocation filtering already applies; the projection catches up later.


def public(row: dict) -> dict:
    row = dict(row)
    row['prediction'] = json.loads(row['prediction']) if row.get('prediction') else None
    row['simulated'] = bool(row.get('simulated'))
    row.pop('asset_path', None)
    return row


def query(*, source='', state='', usage='', label='', start='', end='', page=1, size=30, home=None) -> dict:
    from src.workbench.views import date_bounds
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('無效的分頁')
    lo, hi = date_bounds(start, end)
    clauses = ["NOT EXISTS (SELECT 1 FROM resource_lifecycle r WHERE r.type='research_photo' AND r.id=i.id AND r.state='purged')"]
    values = []
    if source:
        if source not in SOURCES:
            raise ValueError('無效的來源')
        clauses.append('i.source=?'); values.append(source)
    if state:
        if state not in STATES:
            raise ValueError('無效的處理狀態')
        clauses.append('i.state=?'); values.append(state)
    if usage:
        if usage not in ('active', 'test_only', 'withdrawn'):
            raise ValueError('無效的授權狀態')
        clauses.append('i.usage_state=?'); values.append(usage)
    if label:
        clauses.append('(i.stage_label=? OR i.binary_label=?)'); values += [label, label]
    if lo is not None:
        clauses.append('i.received_at>=?'); values.append(lo)
    if hi is not None:
        clauses.append('i.received_at<?'); values.append(hi)
    where = ' AND '.join(clauses)
    with db(_home(home)) as con:
        total = con.execute('SELECT COUNT(*) FROM research_intake i WHERE ' + where, values).fetchone()[0]
        rows = con.execute('SELECT i.*,c.version AS consent_version,c.decided_at AS consent_at,c.withdrawn_at AS consent_withdrawn_at,c.scope AS consent_scope,'
                           "COALESCE((SELECT state FROM resource_lifecycle r WHERE r.type='research_photo' AND r.id=i.id),'active') AS resource_state "
                           'FROM research_intake i JOIN research_consents c ON c.id=i.consent_id WHERE ' + where + ' ORDER BY i.received_at DESC,i.id LIMIT ? OFFSET ?',
                           values + [size, (page - 1) * size]).fetchall()
        tasks = {r['target']: dict(r) for r in con.execute("SELECT target,state,attempts,error,updated FROM cleanup_tasks WHERE kind='research_withdrawal'")}
    items = []
    for r in rows:
        item = public(dict(r))
        item['cleanup'] = tasks.get(r['id'])
        item['tasks'] = eligibility_preview(item)
        items.append(item)
    return {'items': items, 'total': total, 'page': page, 'size': size,
            'retention': '保存至撤回為止（專案負責人決定，無自動到期）', 'note': '模型預測僅供參考，不是標籤；人工確認後才可轉入資料審查。'}


def eligibility_preview(item: dict) -> dict:
    """What the item could serve after promotion and data-review approval (not a training grant)."""
    from src.data.tasks import STAGE_TO_BINARY
    reasons = []
    if item['usage_state'] == 'withdrawn':
        reasons.append('研究授權已撤回')
    if item['usage_state'] == 'test_only':
        reasons.append('模擬資料：只作流程測試，不納入正式訓練')
    if item['state'] not in ('reviewed', 'promoted'):
        reasons.append('尚未完成人工確認')
    binary = list(reasons) + ([] if item['binary_label'] in ('positive', 'negative') else ['二分類標籤未確認'])
    stage = list(reasons) + ([] if item['stage_label'] in ('normal', 'stage1', 'stage2') else ['分期未確認'])
    detection = list(reasons) + ['偵測需在資料審查中完成病灶框或確認無病灶']
    if item['stage_label'] in STAGE_TO_BINARY and item['binary_label'] in ('positive', 'negative') and STAGE_TO_BINARY[item['stage_label']] != item['binary_label']:
        binary.append('分期與二分類矛盾'); stage.append('分期與二分類矛盾')
    return {'binary_classification': binary, 'stage_classification': stage, 'detection': detection}


def get(ident, home=None) -> dict:
    with db(_home(home)) as con:
        row = con.execute('SELECT * FROM research_intake WHERE id=?', (ident,)).fetchone()
    if not row:
        raise FileNotFoundError(ident)
    return dict(row)


def image_path(ident, home=None) -> Path:
    """Management access only: withdrawn, trashed or purged photos are not served."""
    from src.workbench import resources
    row = get(ident, home)
    if row['usage_state'] == 'withdrawn':
        raise ValueError('研究授權已撤回，照片不再提供')
    if resources.record('research_photo', ident)['state'] != 'active':
        raise resources.ResourceUnavailable('research_photo', ident, resources.record('research_photo', ident)['state'])
    if not row['asset_path']:
        raise FileNotFoundError(ident)
    path = (_home(home) / row['asset_path']).resolve()
    if not path.is_relative_to((_home(home) / 'research_intake').resolve()) or not path.is_file():
        raise FileNotFoundError(ident)
    return path


def review(ident, *, revision, state, binary_label, stage_label, quality, subject_alias, subject_confirmed, note, actor, home=None) -> dict:
    from src.data.tasks import STAGE_TO_BINARY, STAGES, QUALITY
    if state not in ('reviewed', 'needs_changes', 'rejected'):
        raise ValueError('無效的審查狀態')
    if binary_label not in ('positive', 'negative', 'unknown') or stage_label not in STAGES or quality not in QUALITY:
        raise ValueError('無效的標籤或品質')
    if stage_label in STAGE_TO_BINARY and STAGE_TO_BINARY[stage_label] != binary_label:
        raise ValueError('分期與二分類標籤不一致')
    if state == 'reviewed' and binary_label == 'unknown':
        raise ValueError('完成確認前需選擇正常或陽性')
    alias = subject_alias.strip()
    if alias and not __import__('re').fullmatch(r'[A-Za-z0-9_\-]{1,40}', alias):
        raise ValueError('個案研究編號只能使用英數、底線與連字號（化名編號，不可填姓名或病歷號）')
    if alias and not subject_confirmed:
        raise ValueError('請確認個案研究編號已核對')
    if not actor:
        raise ValueError('請先設定操作者名稱')
    with db(_home(home)) as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT * FROM research_intake WHERE id=?', (ident,)).fetchone()
        if not row:
            raise FileNotFoundError(ident)
        if row['revision'] != revision:
            raise ValueError('revision conflict: reload before saving')
        if row['usage_state'] == 'withdrawn' or row['state'] in ('promoted', 'withdrawn'):
            raise ValueError('已轉入或已撤回的項目不可再修改；請在資料審查處理')
        con.execute('UPDATE research_intake SET state=?,binary_label=?,stage_label=?,quality=?,subject_alias=?,note=?,reviewer=?,revision=revision+1,updated=? WHERE id=?',
                    (state, binary_label, stage_label, quality, alias, note[:1000], actor, time.time(), ident))
        row = con.execute('SELECT * FROM research_intake WHERE id=?', (ident,)).fetchone()
    audit('research_intake_review', {'intake': ident, 'state': state}, home=_home(home), actor=actor)
    return public(dict(row))


def promote(ident, *, revision, actor, home=None, root=None) -> dict:
    """Explicitly copy a reviewed research photo into data review (pending, not approved)."""
    from src.data import evidence, revocations
    from src.data.dataset import recover_reviews
    from src.workbench.storage import dataset_lock
    if not actor:
        raise ValueError('請先設定操作者名稱')
    root = _root(root)
    row = get(ident, home)
    if row['promoted_image_id']:
        return {'image_id': row['promoted_image_id'], 'status': 'already_promoted'}
    if row['revision'] != revision:
        raise ValueError('revision conflict: reload before saving')
    if row['state'] != 'reviewed':
        raise ValueError('需先完成人工確認（品質、標籤、個案關係）')
    if row['usage_state'] == 'withdrawn':
        raise ValueError('研究授權已撤回')
    if row['quality'] == 'unusable':
        raise ValueError('品質判定不可用的照片不轉入資料審查')
    source = image_path(ident, home)
    value = sha256(source)
    if value != row['image_sha256']:
        raise ValueError('研究照片內容與收件紀錄不符，停止轉入')
    table = revocations.revoked(root)
    if value in table['sha256'] or ident in table['intake']:
        raise ValueError('此照片已被停止使用')
    image_id = 'line_' + value[:16]
    with dataset_lock(root):
        recover_reviews(root)
        rows = read_manifest(root)
        existing = next((r for r in rows if r['sha256'] == value), None)
        if existing:
            raise ValueError(f"相同內容已在資料集中（{existing['image_id']}）；不自動合併不同來源或個案身分，請人工確認")
        if row['subject_alias']:
            reserved = root / 'data/independent_test/manifest.json'
            if reserved.exists() and any(r.get('subject_id') == row['subject_alias'] for r in read_json(reserved)):
                raise ValueError('此個案編號屬於獨立測試集，不可轉入訓練審查（避免資料洩漏）')
        target = root / 'data/pending_review/annotation/images' / f'{image_id}.jpg'
        if target.exists():
            raise ValueError('轉入目的檔已存在；未變更任何檔案')
        target.parent.mkdir(parents=True, exist_ok=True)
        fields = list(rows[0]) if rows else ['image_id', 'sha256', 'image_path', 'annotation_path', 'yolo_path', 'status', 'label_state', 'candidate_group', 'subject_id', 'group_verified', 'reviewer', 'reason', 'updated_at', 'original_paths']
        record = {k: '' for k in fields}
        record.update(image_id=image_id, sha256=value, image_path=target.relative_to(root).as_posix(), status='pending_review', label_state=row['binary_label'],
                      stage_label=row['stage_label'] if row['stage_label'] in ('normal', 'stage1', 'stage2') else '', label_scheme='stage_v1' if row['stage_label'] in ('normal', 'stage1', 'stage2') else '',
                      quality_state=row['quality'], usage_state='test_only' if row['simulated'] else '', candidate_group='', subject_id=row['subject_alias'],
                      group_verified='true' if row['subject_alias'] else 'false', reviewer=actor, reason='LINE 研究收件轉入；待資料審查核准', updated_at=stamp(),
                      original_paths=json.dumps(['research_intake:' + ident], ensure_ascii=False))
        try:
            shutil.copyfile(source, target)
            evidence.append(image_id, {'task': 'classification', 'source': 'line_research_simulated' if row['simulated'] else 'line_research', 'method': 'intake_review',
                                       'actor': row['reviewer'], 'binary': row['binary_label'], 'stage': row['stage_label'], 'intake': ident,
                                       'note': '收件人工確認；模型預測未作為標籤'}, root)
            write_manifest(rows + [record], root)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
    with db(_home(home)) as con:
        con.execute("UPDATE research_intake SET promoted_image_id=?,state='promoted',revision=revision+1,updated=? WHERE id=?", (image_id, time.time(), ident))
    # A withdrawal that raced with promotion still wins.
    if get(ident, home)['usage_state'] == 'withdrawn':
        revocations.revoke('image', image_id, 'withdrawn during promotion', 'intake', root)
    audit('research_intake_promote', {'intake': ident, 'image_id': image_id, 'simulated': bool(row['simulated'])}, home=_home(home), actor=actor)
    _refresh_index()
    return {'image_id': image_id, 'status': 'promoted'}


def run_cleanup(home=None, root=None, limit=5) -> list[dict]:
    """Retryable physical cleanup after withdrawal. Busy locks leave the task pending with a
    visible reason; stop-use was already effective when the task was created."""
    from src.lock import OperationLock
    from src.workbench import managed_files, lifecycle
    from src.workbench.resources import resource_lock
    from src.workbench.storage import file_lock
    root = _root(root)
    with db(_home(home)) as con:
        tasks = [dict(r) for r in con.execute("SELECT * FROM cleanup_tasks WHERE kind='research_withdrawal' AND state IN ('pending','retry') ORDER BY created LIMIT ?", (limit,))]
    done = []
    for task in tasks:
        ident = task['target']
        try:
            row = get(ident, home)
            detail = json.loads(task['detail'])
            image_id = row['promoted_image_id'] or detail.get('promoted_image_id')
            impact = lifecycle.related(ident, 'research_intake', root) if image_id else {'image_ids': [], 'files': [], 'snapshots': []}
            if impact['image_ids'] or impact['files']:
                with OperationLock(), resource_lock(), file_lock(root / 'runtime/data.lock'):
                    lifecycle.remove_derived(impact, 'Research consent withdrawn; research copies removed', root)
                _flag_models(impact['snapshots'], ident, root)
            folder = _home(home) / 'research_intake' / ident
            original = folder / 'original.jpg'
            if original.exists():
                record = managed_files.inspect(original, folder)
                managed_files.remove_verified(original, folder, record, lambda: None)
            try:
                folder.rmdir()
            except OSError:
                pass
            with db(_home(home)) as con:
                con.execute("UPDATE research_intake SET asset_path=NULL,cleanup_state='done',updated=? WHERE id=?", (time.time(), ident))
                con.execute("UPDATE cleanup_tasks SET state='done',attempts=attempts+1,error=NULL,updated=?,detail=? WHERE id=?",
                            (time.time(), json.dumps({**detail, 'impact': impact}, ensure_ascii=False), task['id']))
            audit('research_withdrawal_cleanup', {'intake': ident, 'removed_image_ids': impact['image_ids'], 'snapshots': impact['snapshots']}, home=_home(home))
            done.append({'id': ident, 'state': 'done'})
        except Exception as exc:
            message = '運算或資料鎖忙碌，稍後自動重試' if isinstance(exc, RuntimeError) else type(exc).__name__ + ': ' + str(exc)
            with db(_home(home)) as con:
                con.execute("UPDATE cleanup_tasks SET state='retry',attempts=attempts+1,error=?,updated=? WHERE id=?", (message[:500], time.time(), task['id']))
                con.execute("UPDATE research_intake SET cleanup_state='retry',updated=? WHERE id=?", (time.time(), ident))
            done.append({'id': ident, 'state': 'retry', 'error': message})
    return done


def _flag_models(snapshots, ident, root):
    """Trained models cannot 'forget' data; mark them for reassessment, keeping history."""
    if not snapshots:
        return
    from src.workbench import registry
    from src.workbench.storage import flag
    for path in registry.VERSIONS.glob('*/artifact.json'):
        artifact = read_json(path)
        dataset = artifact.get('extra', {}).get('dataset') or ''
        if any(f'data/yolo/{s}/' in dataset.replace('\\', '/') for s in snapshots):
            flag('model_attention:' + artifact['id'], {'reason': '訓練快照包含已撤回授權的研究照片；需重新評估或重訓。刪除原照片不會移除模型已學到的影響。',
                                                       'intake': ident, 'snapshots': snapshots, 'at': stamp()})
