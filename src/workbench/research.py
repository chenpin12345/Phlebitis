"""Explicit promotion and reserved independent-test imports of authorized research assets."""
import json
import shutil
from PIL import Image
from src.common import ROOT,read_json,write_json,read_manifest,write_manifest,sha256,stamp,inside
from src.workbench.storage import db,audit,file_lock
from src.workbench.lifecycle import asset_path
from src.data.labels import validate,text

def promote(case_id,*,independent=False,subject_id=''):
    with db() as con:
        row=con.execute('SELECT data FROM cases WHERE id=?',(case_id,)).fetchone()
        if not row:raise ValueError('Unknown case')
        case=json.loads(row[0])
        asset=con.execute('SELECT * FROM assets WHERE id=?',(case['asset'],)).fetchone()
    if not asset or asset['category']!='research':raise ValueError('Only explicitly authorized research assets may enter datasets')
    if case['state']!='confirmed':raise ValueError('Human confirmation required')
    source=asset_path(case['asset']);hash_value=sha256(source);ident=hash_value[:16]
    if independent and not subject_id.strip():raise ValueError('Independent test imports require a verified research subject ID')
    boxes=case.get('boxes',[]);validate(boxes)
    if case['label']=='negative' and boxes:raise ValueError('Negative image cannot contain boxes')
    if independent and case['label']=='positive' and not boxes:raise ValueError('Independent positive test images require verified boxes')
    with file_lock(ROOT/'runtime/data.lock'):
        from src.data.dataset import recover_reviews
        recover_reviews(ROOT)
        rows=read_manifest()
        reserved_path=ROOT/'data/independent_test/manifest.json'
        reserved=read_json(reserved_path) if reserved_path.exists() else []
        if any(r['sha256']==hash_value for r in rows):raise ValueError('This image is already in the review catalog')
        if any(r['sha256']==hash_value for r in reserved):raise ValueError('This image is already reserved for independent testing')
        if not independent and subject_id and any(r['subject_id']==subject_id for r in reserved):raise ValueError('Subject is reserved for independent testing')
        if independent and any(r['subject_id']==subject_id for r in rows):raise ValueError('Subject already occurs in training/review data')
        base=ROOT/('data/independent_test' if independent else 'data/pending_review/annotation')
        image=base/'images'/(ident+'.jpg');annotation=base/'annotations'/(ident+'.json')
        lab=base/'annotations'/(ident+'.txt')
        if any(p.exists() for p in (image,annotation,lab)):raise ValueError('Import destination exists; no files changed')
        image.parent.mkdir(parents=True,exist_ok=True);annotation.parent.mkdir(parents=True,exist_ok=True)
        with Image.open(source) as im:w,h=im.size
        shapes=[{'label':'phlebitis','shape_type':'rectangle','points':[[(x-bw/2)*w,(y-bh/2)*h],[(x+bw/2)*w,(y+bh/2)*h]]} for _,x,y,bw,bh in boxes]
        record={k:'' for k in rows[0]}
        record.update(image_id=ident,sha256=hash_value,image_path=image.relative_to(ROOT).as_posix(),annotation_path=annotation.relative_to(ROOT).as_posix(),status='pending_review',label_state=case['label'],candidate_group=ident,subject_id=subject_id,group_verified='true' if subject_id else 'false',reviewer=case['reviewer'],reason=case.get('notes') or 'authorized research import',updated_at=stamp(),original_paths=json.dumps(['research_asset:'+case['asset']]))
        manifest=reserved_path if independent else ROOT/'data/manifest.csv'
        journal=ROOT/'runtime/review_transactions'/stamp();journal.mkdir(parents=True)
        entries=[]
        for i,p in enumerate((image,annotation,lab,manifest)):
            backup=f'{i}.bak' if p.exists() else None
            if backup:shutil.copy2(p,journal/backup)
            entries.append({'path':p.relative_to(ROOT).as_posix(),'backup':backup})
        tx={'state':'pending','image_id':ident,'files':entries,'logs_before':[p.name for p in (ROOT/'data/reviews').glob('*.json')]}
        write_json(journal/'journal.json',tx)
        try:
            shutil.copy2(source,image);write_json(annotation,{'imageWidth':w,'imageHeight':h,'shapes':shapes})
            if independent:
                lab.write_text(text(boxes),encoding='utf-8')
                record.update(yolo_path=lab.relative_to(ROOT).as_posix(),status='independent_test')
                write_json(reserved_path,reserved+[record])
            else:write_manifest(rows+[record])
            tx['state']='committed';write_json(journal/'journal.json',tx)
            for p in journal.glob('*.bak'):p.unlink()
        except BaseException:
            recover_reviews(ROOT);raise
    audit('import_independent_test' if independent else 'promote_case',{'case':case_id,'image_id':ident,'asset':case['asset']})
    return record

def build_independent():
    import yaml
    from src.data.dataset import latest_dataset,validate_split
    with file_lock(ROOT/'runtime/data.lock'):
        reserved=read_json(ROOT/'data/independent_test/manifest.json')
        if {r['label_state'] for r in reserved}!={'positive','negative'}:raise ValueError('Independent test pool needs both classes; do not manufacture a test split from existing data')
        original=latest_dataset(0);split=validate_split(original)
        train=split['members']['train']+split['members']['val']
        if {r['subject_id'] for r in reserved}&{r['group'] for r in train}:raise ValueError('Independent subject overlaps existing dataset')
        version='independent_'+stamp();base=ROOT/'data/yolo'/version;target=base/'fold0';members={'train':[],'val':[]}
        for name,rows in [('train',train),('val',reserved)]:
            for r in rows:
                ip=target/'images'/name/(r['image_id']+'.jpg');lp=target/'labels'/name/(r['image_id']+'.txt')
                ip.parent.mkdir(parents=True,exist_ok=True);lp.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(inside(r['image_path']),ip);shutil.copy2(inside(r.get('label_path') or r['yolo_path']),lp)
                members[name].append({'image_id':r['image_id'],'group':r.get('group') or r['subject_id'],'label_state':r['label_state'],'image_path':ip.relative_to(ROOT).as_posix(),'label_path':lp.relative_to(ROOT).as_posix(),'dataset_sha256':sha256(ip),'label_sha256':sha256(lp)})
        dataset=target/'dataset.yaml';dataset.write_text(yaml.safe_dump({'path':str(target.resolve()),'train':'images/train','val':'images/val','names':{0:'phlebitis'}}),encoding='utf-8')
        entry={'schema_version':2,'fold':0,'dataset':dataset.relative_to(ROOT).as_posix(),'members':members,'demo_only':split['demo_only'],'purpose':'independent_test'}
        write_json(target/'split.json',entry);entry['split_sha256']=sha256(target/'split.json')
        info={'schema_version':2,'version':version,'demo_only':split['demo_only'],'purpose':'independent_test','folds':[entry]}
        write_json(base/'dataset_version.json',info)
        audit('build_independent_test',{'version':version,'members':len(reserved)})
        return info
