import json
import time
import uuid
from src.common import ROOT, inside, write_json,read_manifest,write_manifest,stamp
from src.workbench.storage import HOME, db, audit, flag
from src.inference.engine import decode_image, encode_result
from src.common import read_json

def upload(raw,*,research=False,authorization='',purpose=''):
    image=decode_image(raw,read_json(ROOT/'configs/service.json'))
    if research and (not authorization.strip() or not purpose.strip()): raise ValueError('研究回收需要授權紀錄與用途')
    ident=uuid.uuid4().hex; category='research' if research else 'simulation'
    path=HOME/'assets'/category/(ident+'.jpg'); path.parent.mkdir(parents=True,exist_ok=True)
    # Keep full-resolution corrected pixels for annotations, strip identifying EXIF.
    image.save(path,format='JPEG',quality=95)
    now=time.time(); expires=now+(30*86400 if research else 3600)
    metadata={'authorization':authorization,'purpose':purpose,'source':'local_upload','withdrawn':False}
    with db() as con: con.execute('INSERT INTO assets VALUES(?,?,?,?,?,?)',(ident,category,str(path.relative_to(ROOT)),now,expires,json.dumps(metadata,ensure_ascii=False)))
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

def related(ident):
    rows=[r for r in read_manifest() if 'research_asset:'+ident in json.loads(r.get('original_paths') or '[]')]
    independent=ROOT/'data/independent_test/manifest.json'
    if independent.exists():rows += [r for r in read_json(independent) if 'research_asset:'+ident in json.loads(r.get('original_paths') or '[]')]
    ids={r['image_id'] for r in rows}; files=set(); snapshots=[]
    for row in rows:
        for k in ('image_path','annotation_path','yolo_path'):
            if row.get(k):files.add(row[k])
    for p in (ROOT/'data/yolo').glob('*/dataset_version.json'):
        info=read_json(p);found=False
        for fold in info['folds']:
            for members in fold['members'].values():
                for m in members:
                    if m['image_id'] in ids:
                        files.update([m['image_path'],m['label_path']]);found=True
        if found:snapshots.append(p.parent.name)
    for ident in ids:
        for p in (ROOT/'runs/workbench/evaluations').glob('*/'+ident+'.jpg'):files.add(p.relative_to(ROOT).as_posix())
    # Ultralytics mosaics are also image copies, unlike numeric reports/checkpoints.
    for p in (ROOT/'runs/workbench/jobs').glob('*/experiment.json'):
        experiment=read_json(p)
        if any(m['image_id'] in ids for members in experiment.get('split',{}).get('members',{}).values() for m in members):
            for picture in (p.parent/'training').rglob('*.jpg'):files.add(picture.relative_to(ROOT).as_posix())
    for p in (ROOT/'runs/workbench/evaluations').glob('*/report.json'):
        if any(s['image_id'] in ids for s in read_json(p).get('samples',[])):
            for picture in (p.parent/'detection').rglob('*.jpg'):files.add(picture.relative_to(ROOT).as_posix())
    for p in (HOME/'features').glob('*.json'):
        if read_json(p).get('image_id') in ids:files.update([p.relative_to(ROOT).as_posix(),p.with_suffix('.npy').relative_to(ROOT).as_posix()])
    return {'image_ids':sorted(ids),'files':sorted(files),'snapshots':snapshots,'reproducibility_lost':bool(snapshots)}

def cleanup(ids):
    from src.lock import OperationLock
    from src.workbench.storage import file_lock
    with OperationLock(),file_lock(ROOT/'runtime/data.lock'):
        return _cleanup(ids)

def _cleanup(ids):
    preview={x['id']:x for x in preview_cleanup()['assets']}
    if set(ids)-set(preview): raise ValueError('Cleanup list changed; preview again')
    for ident in ids:
        item=preview[ident];path=inside(item['path'],ROOT)
        if not path.is_relative_to(HOME/'assets'): raise ValueError('Cleanup outside managed assets')
        impact=item['impact']
        states_path=ROOT/'data/snapshot_states.json'
        states=read_json(states_path) if states_path.exists() else {}
        for snapshot in impact['snapshots']:states[snapshot]={'status':'withdrawn','reason':'Authorized research data expired or was withdrawn; original pixels removed','at':stamp()}
        write_json(states_path,states)
        for name in impact['files']:
            file=inside(name,ROOT)
            allowed=[ROOT/'data/approved',ROOT/'data/pending_review',ROOT/'data/excluded',ROOT/'data/yolo',ROOT/'data/independent_test',ROOT/'runs/workbench/evaluations',ROOT/'runs/workbench/jobs',HOME/'features']
            if not any(file.is_relative_to(base) for base in allowed):raise ValueError('Derived data cleanup outside allowed managed locations')
            file.unlink(missing_ok=True)
        if impact['image_ids']:
            write_manifest([r for r in read_manifest() if r['image_id'] not in impact['image_ids']])
            independent=ROOT/'data/independent_test/manifest.json'
            if independent.exists():write_json(independent,[r for r in read_json(independent) if r['image_id'] not in impact['image_ids']])
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
    return {'deleted':ids}

def withdraw(ident):
    from src.lock import OperationLock
    from src.workbench.storage import file_lock
    # Acquire both leases before changing validity. A busy response must not leave
    # an expired-but-still-confirmed case that background regression can select.
    with OperationLock(),file_lock(ROOT/'runtime/data.lock'):
        with db() as con:
            row=con.execute('SELECT metadata FROM assets WHERE id=?',(ident,)).fetchone()
            if not row: raise ValueError('Unknown asset')
            meta=json.loads(row[0]);meta['withdrawn']=True
            con.execute('UPDATE assets SET expires=?,metadata=? WHERE id=?',(time.time()-1,json.dumps(meta),ident))
        audit('withdraw',{'asset':ident})
        return _cleanup([ident])

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
