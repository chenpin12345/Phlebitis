import json
import time
import uuid
from src.common import ROOT, inside, write_json,read_manifest,write_manifest,stamp
from src.common import config_path
from src.workbench.storage import HOME, db, audit, flag
from src.inference.engine import decode_image, encode_result
from src.common import read_json
from src.workbench.resources import resource_lock, guarded, invalidate_capacity

def upload(raw,*,research=False,authorization='',purpose=''):
    image=decode_image(raw,read_json(config_path('service.json',ROOT)))
    if research and (not authorization.strip() or not purpose.strip()): raise ValueError('研究回收需要授權紀錄與用途')
    ident=uuid.uuid4().hex; category='research' if research else 'simulation'
    path=HOME/'assets'/category/(ident+'.jpg'); path.parent.mkdir(parents=True,exist_ok=True)
    # Keep full-resolution corrected pixels for annotations, strip identifying EXIF.
    image.save(path,format='JPEG',quality=95)
    now=time.time(); expires=now+(30*86400 if research else 3600)
    metadata={'authorization':authorization,'purpose':purpose,'source':'local_upload','withdrawn':False}
    with db() as con: con.execute('INSERT INTO assets(id,category,path,created,expires,metadata) VALUES(?,?,?,?,?,?)',(ident,category,str(path.relative_to(ROOT)),now,expires,json.dumps(metadata,ensure_ascii=False)))
    audit('upload',{'asset':ident,'category':category,'expires':expires})
    return {'id':ident,'category':category,'expires':expires,'width':image.width,'height':image.height}

def asset_path(ident,allow_expired=False):
    with db() as con: row=con.execute('SELECT * FROM assets WHERE id=?',(ident,)).fetchone()
    if not row: raise ValueError('Unknown asset')
    if row['expires']<=time.time() and not allow_expired: raise ValueError('Asset expired; use a new authorized upload')
    p=inside(row['path'],ROOT)
    if not p.is_relative_to(HOME/'assets') or not p.is_file(): raise ValueError('Asset unavailable')
    return p

def preview_cleanup():
    with db() as con:
        assets=[dict(r) for r in con.execute('SELECT * FROM assets WHERE expires<=?',(time.time(),))]
    for asset in assets:asset['impact']=related(asset['id'])
    return {'assets':assets,'protected':['archive','pre-existing research data','models/versions'],'note':'只清理已到期的工作台回收／模擬資料與其受管理副本；既有資料不適用 30 天期限。'}

def related(ident,tag='research_asset',root=None):
    from src import common
    base=root or ROOT
    manifest=common.read_manifest(root) if root else read_manifest()
    rows=[r for r in manifest if tag+':'+ident in json.loads(r.get('original_paths') or '[]')]
    independent=base/'data/independent_test/manifest.json'
    if independent.exists():rows += [r for r in read_json(independent) if tag+':'+ident in json.loads(r.get('original_paths') or '[]')]
    ids={r['image_id'] for r in rows}; files=set(); snapshots=[]
    for row in rows:
        for k in ('image_path','annotation_path','yolo_path'):
            if row.get(k):files.add(row[k])
    for p in (base/'data/yolo').glob('*/dataset_version.json'):
        info=read_json(p);found=False
        for fold in info['folds']:
            for members in fold['members'].values():
                for m in members:
                    if m['image_id'] in ids:
                        files.update(x for x in (m.get('image_path'),m.get('label_path')) if x);found=True
        if found:snapshots.append(p.parent.name)
    for ident in ids:
        for p in (base/'runs/workbench/evaluations').glob('*/'+ident+'.jpg'):files.add(p.relative_to(base).as_posix())
    # Ultralytics mosaics are also image copies, unlike numeric reports/checkpoints.
    for p in (base/'runs/workbench/jobs').glob('*/experiment.json'):
        experiment=read_json(p)
        if any(m['image_id'] in ids for members in experiment.get('split',{}).get('members',{}).values() for m in members):
            for picture in (p.parent/'training').rglob('*.jpg'):files.add(picture.relative_to(base).as_posix())
    for p in (base/'runs/workbench/evaluations').glob('*/report.json'):
        if any(s['image_id'] in ids for s in read_json(p).get('samples',[])):
            for picture in (p.parent/'detection').rglob('*.jpg'):files.add(picture.relative_to(base).as_posix())
    for p in (HOME/'features').glob('*.json'):
        if read_json(p).get('image_id') in ids:files.update([p.relative_to(base).as_posix(),p.with_suffix('.npy').relative_to(base).as_posix()])
    return {'image_ids':sorted(ids),'files':sorted(files),'snapshots':snapshots,'reproducibility_lost':bool(snapshots)}

def remove_derived(impact,reason,root=None):
    """Remove managed copies derived from withdrawn research data. Callers hold the
    compute, lifecycle and dataset locks. Affected snapshots are marked withdrawn first."""
    from src import common
    base=root or ROOT
    states_path=base/'data/snapshot_states.json'
    states=read_json(states_path) if states_path.exists() else {}
    for snapshot in impact['snapshots']:states[snapshot]={'status':'withdrawn','reason':reason,'at':stamp()}
    write_json(states_path,states)
    for name in impact['files']:
        file=inside(name,base)
        allowed=[base/'data/approved',base/'data/pending_review',base/'data/excluded',base/'data/yolo',base/'data/independent_test',base/'runs/workbench/evaluations',base/'runs/workbench/jobs',HOME/'features']
        if not any(file.is_relative_to(area) for area in allowed):raise ValueError('Derived data cleanup outside allowed managed locations')
        file.unlink(missing_ok=True)
        invalidate_capacity(file)
    if impact['image_ids']:
        kept=[r for r in (common.read_manifest(root) if root else read_manifest()) if r['image_id'] not in impact['image_ids']]
        common.write_manifest(kept,root) if root else write_manifest(kept)
        independent=base/'data/independent_test/manifest.json'
        if independent.exists():write_json(independent,[r for r in read_json(independent) if r['image_id'] not in impact['image_ids']])

def cleanup(ids):
    from src.lock import OperationLock
    from src.workbench.storage import file_lock
    with OperationLock(),resource_lock(),file_lock(ROOT/'runtime/data.lock'):
        return _cleanup(ids)

def _cleanup(ids):
    preview={x['id']:x for x in preview_cleanup()['assets']}
    if set(ids)-set(preview): raise ValueError('Cleanup list changed; preview again')
    for ident in ids:
        item=preview[ident];path=inside(item['path'],ROOT)
        if not path.is_relative_to(HOME/'assets'): raise ValueError('Cleanup outside managed assets')
        impact=item['impact']
        remove_derived(impact,'Authorized research data expired or was withdrawn; original pixels removed')
        path.unlink(missing_ok=True)
        with db() as con:
            con.execute('DELETE FROM assets WHERE id=?',(ident,))
            rows=con.execute('SELECT id,data FROM cases').fetchall()
            for row in rows:
                data=json.loads(row['data'])
                if data.get('asset')==ident:
                    data.update(state='withdrawn',reproducible=False)
                    con.execute('UPDATE cases SET data=? WHERE id=?',(json.dumps(data,ensure_ascii=False),row['id']))
        audit('delete_expired',{'asset':ident,'scope':'managed_copy_only','reproducibility':'referencing cases and affected snapshots unavailable','impact':impact})
    from src.workbench.queries import data_index,images
    data_index.invalidate(ROOT);images.clear(ROOT);data_index.request_rebuild(ROOT)
    return {'deleted':ids}

def withdraw(ident):
    from src.lock import OperationLock
    from src.workbench.storage import file_lock
    # Acquire both leases before changing validity. A busy response must not leave
    # an expired-but-still-confirmed case that background regression can select.
    with OperationLock(),resource_lock(),file_lock(ROOT/'runtime/data.lock'):
        with db() as con:
            row=con.execute('SELECT metadata FROM assets WHERE id=?',(ident,)).fetchone()
            if not row: raise ValueError('Unknown asset')
            meta=json.loads(row[0]);meta['withdrawn']=True
            con.execute('UPDATE assets SET expires=?,metadata=? WHERE id=?',(time.time()-1,json.dumps(meta),ident))
        audit('withdraw',{'asset':ident})
        return _cleanup([ident])

@guarded
def expire_temporary():
    """Automatic expiry is limited to newly created ephemeral simulation media."""
    from src.workbench.jobs import listing,folder
    jobs=listing(limit=None,include_trashed=True);active={j['config'].get('asset') for j in jobs if j['state'] in ('queued','running','cancelling')}
    with db() as con:
        rows=con.execute("SELECT * FROM assets WHERE category='simulation' AND expires<=?",(time.time(),)).fetchall()
        for row in rows:
            if row['id'] in active:continue
            p=inside(row['path'],ROOT)
            if p.is_relative_to(HOME/'assets/simulation'):p.unlink(missing_ok=True)
            con.execute('DELETE FROM assets WHERE id=?',(row['id'],))
        con.execute('DELETE FROM events WHERE updated<?',(time.time()-86400,))
    for j in jobs:
        if j['kind']=='predict' and j.get('result') and j['result'].get('expires',0)<time.time():
            (folder(j['id'])/'result.jpg').unlink(missing_ok=True)
            invalidate_capacity(folder(j['id'])/'result.jpg')
    # Clean originals kept only for a consent decision expire with their simulated result.
    from src.line_bot.service import Store
    pending=HOME/'line_pending'
    if pending.exists():
        s=Store(HOME/'simulation.sqlite3',reconcile=False)
        try:
            for p in pending.glob('*.jpg'):
                expires=s.expiry(p.stem)
                if not expires or expires<=time.time():p.unlink(missing_ok=True)
        finally:s.close()
