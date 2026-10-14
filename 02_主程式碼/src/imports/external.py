"""Read-only scan and import of explicitly configured external photo folders.

Only sources listed in configs/import_sources.json may be read.  The source tree is
never moved, renamed, overwritten or deleted.  Files that must be added are copied
into inbox/photos/<batch>/ and then committed by the existing import service, so the
project keeps one import pipeline.  Images whose bytes already exist only receive a
source alias (display name) and filename-rule evidence; nothing is imported twice.
"""
from __future__ import annotations

import io
import json
import os
import time
import uuid
from pathlib import Path, PurePosixPath

from PIL import Image, ImageOps, UnidentifiedImageError

from src.common import inside, read_json, read_manifest, stamp, write_json
from src.common import config_path
from src.imports import service
from src.workbench.storage import dataset_lock, file_lock

KIND = 'external_photos'
CONFIG = 'configs/import_sources.json'
IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png', '.webp')
NEAR_DISTANCE = 4
CATEGORY_NAMES = {
    'existing': '已存在（內容相同）', 'addable': '可補入', 'same_name': '同名不同內容（獨立保存）',
    'near_duplicate': '近似重複候選（仍獨立保存，請人工確認）', 'pixel_duplicate': '校正方向後像素相同（隔離，不自動合併）',
    'duplicate_in_source': '來源內重複內容（記為別名）', 'unsupported': '不支援的檔案', 'corrupt': '損毀或無法解碼',
    'label_conflict': '標籤或來源衝突',
}


def sources(root: Path) -> dict:
    data = read_json(config_path('import_sources.json', root))
    if data.get('schema_version') != 1:
        raise ValueError('外部來源設定版本不支援')
    return data['sources']


def source_base(root: Path, key: str) -> tuple[Path, dict]:
    config = sources(root).get(key)
    if not config:
        raise ValueError('未設定的外部來源；只允許讀取 configs/import_sources.json 明列的資料夾')
    base = Path(config['path'])
    if not base.is_absolute() or not base.is_dir():
        raise FileNotFoundError('外部來源資料夾不存在')
    for p in [*reversed(base.parents), base]:
        s = p.lstat()
        if p.is_symlink() or getattr(s, 'st_file_attributes', 0) & 0x400:
            raise ValueError('外部來源路徑包含連結或 reparse point，拒絕讀取')
    return base, config


def public_sources(root: Path) -> list[dict]:
    return [{'key': k, 'name': v.get('name', k), 'label_rule': v.get('label_rule')} for k, v in sources(root).items()]


def _read_external(path: Path, base: Path) -> tuple[bytes, list]:
    from src.workbench.managed_files import opened
    from src.workbench.queries.data_index import stat_key
    before = stat_key(path)
    with opened(path, base) as (stream, _):
        s = os.fstat(stream.fileno())
        if s.st_nlink != 1:
            raise ValueError('不接受共享硬連結')
        data = stream.read()
    if stat_key(path) != before:
        raise ValueError('來源正在變更，請稍後重新掃描')
    return data, before


def fingerprint(data: bytes) -> dict:
    """EXIF-corrected pixel hash (exact) and a 64-bit difference hash (near-duplicate candidates)."""
    import hashlib
    with Image.open(io.BytesIO(data)) as im:
        if im.format not in ('JPEG', 'PNG', 'WEBP') or im.width * im.height > service.MAX_PIXELS or min(im.size) < 64:
            raise ValueError('圖片格式或尺寸不合規則（64 px 至 2500 萬像素）')
        orientation = im.getexif().get(274, 1)
        image = ImageOps.exif_transpose(im).convert('RGB')
    pixel = hashlib.sha256(f'{image.width}x{image.height}'.encode() + image.tobytes()).hexdigest()
    small = image.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
    values = list(small.tobytes())
    bits = ''.join('1' if values[r * 9 + c] > values[r * 9 + c + 1] else '0' for r in range(8) for c in range(8))
    return {'pixel_sha256': pixel, 'dhash': f'{int(bits, 2):016x}', 'size': [image.width, image.height], 'orientation': orientation}


def _distance(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count('1')


def project_fingerprints(root: Path, rows: list[dict], progress=None) -> dict:
    """Pixel fingerprints of project images, cached by content hash (never recomputed per page view)."""
    path = root / 'runtime/imports/pixel_cache.json'
    cache = read_json(path) if path.exists() else {}
    changed = False
    for n, row in enumerate(rows):
        if row['sha256'] in cache:
            continue
        try:
            cache[row['sha256']] = fingerprint(inside(row['image_path'], root).read_bytes())
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            cache[row['sha256']] = {'error': str(exc)[:200]}
        changed = True
        if progress:
            progress(n + 1, len(rows))
    if changed:
        write_json(path, cache)
    return cache


def _known_names(root: Path, rows: list[dict]) -> dict[str, set]:
    from src.data import sources as names
    result: dict[str, set] = {}
    for row in rows:
        for original in json.loads(row.get('original_paths') or '[]'):
            result.setdefault(PurePosixPath(str(original).replace('\\', '/')).name, set()).add(row['image_id'])
    for ident, entry in names.load(root)['images'].items():
        for alias in entry.get('aliases', []):
            result.setdefault(alias['filename'], set()).add(ident)
    return result


def scan(root: Path, key: str, session: str = 'cli', ident: str | None = None, actor=None) -> dict:
    ident = ident or uuid.uuid4().hex
    with file_lock(root / 'runtime/imports' / (ident + '.lock')):
        return _scan(root, key, session, ident, actor)


def _scan(root, key, session, ident, actor):
    from src.data import filename_rules
    from src.data.tasks import STAGE_TO_BINARY
    item = {'id': ident, 'kind': KIND, 'batch': key, 'created': time.time(), 'session': session, 'state': 'scanning', 'items': [], 'operator': actor, 'phase': '列出檔案', 'processed': 0}
    service.save(root, item)
    try:
        base, config = source_base(root, key)
        rule = config.get('label_rule')
        files = []
        for directory, dirs, names_here in os.walk(base, followlinks=False):
            for d in list(dirs):
                p = Path(directory) / d
                if p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400:
                    dirs.remove(d)
                    files.append((p, 'link'))
            for name in sorted(names_here):
                files.append((Path(directory) / name, None))
                if len(files) > service.MAX_FILES:
                    raise ValueError('來源超過 1000 個檔案，請分批處理')
        files.sort(key=lambda x: x[0].relative_to(base).as_posix())
        rows = read_manifest(root)
        by_sha = {r['sha256']: r for r in rows}
        known_names = _known_names(root, rows)
        item.update(total=len(files), phase='計算內容雜湊與像素指紋')
        service.save(root, item)
        project = None
        output, seen = [], {}
        for n, (path, problem) in enumerate(files):
            rel = path.relative_to(base).as_posix()
            entry = {'name': rel, 'filename': path.name, 'notes': []}
            try:
                if problem == 'link':
                    raise ValueError('連結或 reparse point，不讀取')
                if path.suffix.lower() == '.csv':
                    entry.update(category='unsupported', action='reject', reason='熱像儀溫度 CSV：不是影像，也不是分期或個案標籤；不匯入')
                    output.append(entry)
                    continue
                if path.suffix.lower() not in IMAGE_SUFFIXES:
                    raise ValueError('不支援的檔案格式')
                if path.stat().st_size > service.MAX_PHOTO:
                    raise ValueError('單張圖片超過 50 MiB')
                data, identity = _read_external(path, base)
                import hashlib
                digest_value = hashlib.sha256(data).hexdigest()
                entry.update(sha256=digest_value, bytes=len(data), identity=identity)
                try:
                    entry.update(fingerprint(data))
                except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
                    entry.update(category='corrupt', action='reject', reason='無法解碼圖片：' + type(exc).__name__)
                    output.append(entry)
                    continue
                label = filename_rules.parse(rule, rel) if rule else None
                entry['label'] = label
                if label and label['value'] == 'unknown':
                    entry['notes'].append('檔名規則無法判定分期：' + '；'.join(label['reasons']))
                if digest_value in by_sha:
                    row = by_sha[digest_value]
                    entry.update(category='existing', action='alias', existing_image_id=row['image_id'], existing_status=row['status'], existing_label=row['label_state'],
                                 reason='內容相同，已在專案中；只補記來源名稱與檔名規則證據，不重複匯入')
                    expected = STAGE_TO_BINARY.get(label['value']) if label else None
                    if expected and row['label_state'] in ('positive', 'negative') and expected != row['label_state']:
                        entry.update(category='label_conflict', reason='檔名分期與既有二分類標籤矛盾；只記錄雙方證據，不覆蓋既有標籤')
                    if label and row.get('stage_label') and label['value'] != 'unknown' and row['stage_label'] != label['value']:
                        entry.update(category='label_conflict', reason='檔名分期與已確認分期不同；不覆蓋既有標籤')
                elif digest_value in seen:
                    entry.update(category='duplicate_in_source', action='alias', same_as=seen[digest_value], reason='與來源中另一個檔案內容相同；只匯入一次並保留兩個來源名稱')
                else:
                    if project is None:
                        item['phase'] = '比對專案照片像素指紋（首次較久，之後使用快取）'
                        service.save(root, item)
                        project = project_fingerprints(root, rows)
                    pixel = [r['image_id'] for r in rows if project.get(r['sha256'], {}).get('pixel_sha256') == entry['pixel_sha256']]
                    near = sorted(({'image_id': r['image_id'], 'distance': _distance(project[r['sha256']]['dhash'], entry['dhash'])}
                                   for r in rows if project.get(r['sha256'], {}).get('dhash')), key=lambda x: x['distance'])
                    near = [x for x in near if x['distance'] <= NEAR_DISTANCE][:5]
                    if pixel:
                        entry.update(category='pixel_duplicate', action='hold', pixel_matches=pixel, reason='檔案不同但校正方向後像素完全相同；隔離待人工決定，不自動合併')
                    elif near:
                        entry.update(category='near_duplicate', action='add', near=near, reason='近似重複候選；仍以獨立照片補入，請人工確認是否同一次拍攝')
                    elif path.name in known_names:
                        entry.update(category='same_name', action='add', name_matches=sorted(known_names[path.name]), reason='與既有照片同名但內容不同；以新的 image_id 獨立保存')
                    else:
                        entry.update(category='addable', action='add', reason='專案中沒有相同內容；可補入待審查區，標籤保持未確認')
                    seen[digest_value] = rel
            except (OSError, ValueError) as exc:
                entry.update(category='unsupported' if 'link' in str(problem or '') or '格式' in str(exc) else 'corrupt', action='reject', reason=str(exc).replace(str(base), '來源資料夾'))
            output.append(entry)
            item['processed'] = n + 1
            if n % 8 == 0:
                service.save(root, item)
        item['items'] = output
        item['summary'] = {c: sum(e['category'] == c for e in output) for c in CATEGORY_NAMES}
        item['category_names'] = CATEGORY_NAMES
        item['bytes'] = sum(e.get('bytes', 0) for e in output if e['action'] == 'add')
        item['required_free_bytes'] = item['bytes'] * 3 + 64 * 1024 ** 2
        item.update(state='ready', expires=time.time() + 1800, phase='完成', source_name=config.get('name', key), label_rule=rule, scanned_at=stamp())
    except Exception as exc:
        item.update(state='failed', error=str(exc))
    service.save(root, item)
    return item


def commit(root: Path, ident: str, idem: str, session: str = 'cli', retry: bool = False) -> dict:
    if not idem or len(idem) > 200:
        raise ValueError('必須提供有效的冪等鍵')
    item = service.load(root, ident)
    if item['kind'] != KIND:
        raise ValueError('不是外部來源匯入')
    if item['session'] != session:
        raise ValueError('匯入預覽不屬於目前管理會話')
    with file_lock(root / 'runtime/imports' / (ident + '.lock')):
        item = service.load(root, ident)
        if item['state'] == 'completed':
            return item
        if not retry and (item['state'] not in ('ready', 'queued') or (item['state'] == 'ready' and time.time() > item['expires'])):
            raise ValueError('預覽已過期或非可提交狀態')
        if item.get('idem') and item['idem'] != idem:
            raise ValueError('操作冪等鍵不相符')
        item.update(state='running', idem=idem, error=None)
        service.save(root, item)
        try:
            _commit(root, item, session)
            if source_base(root, item['batch'])[1].get('auto_apply'):
                # Authorized source: classify from filenames now (idempotent; human results kept).
                item['phase'] = '依授權檔名規則分類'
                service.save(root, item)
                from src.data.source_rules import apply_authorized_rules
                item['rule_summary'] = apply_authorized_rules(root)['summary']
            item.update(state='completed', phase='完成', completed_at=stamp())
            service.save(root, item)
            write_json(root / 'runtime/imports/receipts' / (ident + '.json'), {k: v for k, v in item.items() if k not in ('session', 'idem')})
            from src.workbench.storage import audit
            audit('external_import_completed', {'import': ident, 'source': item['batch'], 'added': len([e for e in item['items'] if e['action'] == 'add']),
                                                 'aliases': len([e for e in item['items'] if e['action'] == 'alias'])}, home=root / 'runtime/workbench', actor=item.get('operator'))
        except Exception as exc:
            item.update(state='failed', error=str(exc).replace(str(root), '專案'))
            service.save(root, item)
        return item


def _commit(root, item, session):
    import shutil
    from src.data import evidence, sources as names
    base, config = source_base(root, item['batch'])
    batch = f"{item['batch']}-{item['id'][:12]}"
    adds = [e for e in item['items'] if e['action'] == 'add']
    mapping = {e['sha256']: e['existing_image_id'] for e in item['items'] if e.get('existing_image_id')}
    if adds:
        if shutil.disk_usage(root).free < item['required_free_bytes']:
            raise OSError('可用磁碟空間不足，尚未提交正式資料')
        inbox = service.batch_path(root, 'photos', batch)
        item['phase'] = '複製到 inbox（來源保持不變）'
        service.save(root, item)
        for entry in adds:
            target = service.safe(inbox / entry['name'], root)
            if target.exists():
                from src.common import sha256
                if sha256(target) != entry['sha256']:
                    raise ValueError('inbox 中已有不同內容的同名檔案，停止提交')
                continue
            source = base / entry['name']
            data, identity = _read_external(source, base)
            import hashlib
            if hashlib.sha256(data).hexdigest() != entry['sha256'] or identity != entry['identity']:
                raise ValueError(f"來源於預覽後變更：{entry['name']}；請重新掃描")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.partial')
            temporary.write_bytes(data)
            os.replace(temporary, target)
        inner = item.get('inner_import')
        if inner:
            previous = service.load(root, inner)
            # An unsubmitted inner preview that expired is simply re-created; nothing was written.
            if previous['state'] == 'ready' and time.time() > previous['expires'] and not previous.get('idem'):
                inner = None
        if not inner:
            item['phase'] = '既有匯入服務預覽'
            inner_item = service.preview(root, 'photos', batch, session=session, actor=item.get('operator'))
            if inner_item['state'] != 'ready':
                raise ValueError('內部匯入預覽失敗：' + str(inner_item.get('error')))
            item['inner_import'] = inner = inner_item['id']
            service.save(root, item)
        inner_item = service.load(root, inner)
        if inner_item['session'] != session:
            inner_item['session'] = session
            service.save(root, inner_item)
        if inner_item['state'] != 'completed':
            item['phase'] = '既有匯入服務提交（暫存、驗證、寫入清單）'
            service.save(root, item)
            inner_item = service.commit(root, inner, 'external-inner:' + item['id'], session=session, retry=inner_item['state'] in ('failed', 'needs_check', 'running', 'queued'))
        if inner_item['state'] != 'completed':
            raise ValueError('內部匯入未完成：' + str(inner_item.get('error')))
        for entry in inner_item['items']:
            if entry.get('sha256'):
                mapping[entry['sha256']] = entry.get('existing_image_id') or entry.get('image_id')
        item['inbox_batch'] = batch
    item['phase'] = '補記來源名稱與檔名規則證據'
    service.save(root, item)
    with dataset_lock(root):
        data = names.load(root)
        rows = {r['image_id'] for r in read_manifest(root)}
        for entry in item['items']:
            if entry['action'] not in ('add', 'alias') or not entry.get('sha256'):
                continue
            image_id = mapping.get(entry['sha256'])
            if not image_id or image_id not in rows:
                entry.update(result='未找到對應的專案照片，未補記')
                continue
            names.add_alias(data['images'], image_id, {'source': config.get('alias_source', item['batch']), 'relative_path': entry['name'],
                                                         'source_sha256': entry['sha256'], 'batch': item['id'], 'label_rule': config.get('label_rule')})
            entry['image_id'] = image_id
            label = entry.get('label')
            if label:
                evidence.append(image_id, {'task': 'stage_classification', 'value': label['value'], 'method': 'rule_prefill', 'source': config.get('alias_source', item['batch']),
                                           'rule_version': label['rule'], 'relative_path': entry['name'], 'side': label.get('side'), 'reasons': label.get('reasons', []),
                                           'confirmation': 'pending_human_review', 'import': item['id']}, root,
                                dedupe_key=f"{label['rule']}:{entry['sha256']}:{entry['name']}")
            entry['result'] = '已補入並記錄來源名稱' if entry['action'] == 'add' else '已補記來源名稱（未重複匯入）'
        names.save(data, root)
    from src.workbench.queries import data_index
    data_index.invalidate(root)
    data_index.request_rebuild(root)


def recover(root: Path) -> None:
    with service.store(root) as con:
        ids = [r[0] for r in con.execute("SELECT id FROM imports WHERE kind=? AND state IN ('queued','running','scanning')", (KIND,))]
    for ident in ids:
        try:
            with file_lock(root / 'runtime/imports' / (ident + '.lock')):
                item = service.load(root, ident)
                if item['state'] in ('queued', 'running'):
                    item.update(state='needs_check', error='服務中斷，請明確重試；已完成步驟不會重做')
                else:
                    item.update(state='failed', error='掃描中斷，請重新掃描')
                service.save(root, item)
        except RuntimeError:
            pass
