"""Report summaries and samples are independently paginated SQL projections."""
import json
from src.common import read_json
from src.workbench.queries.data_index import connection,stat_key

PREFIX='runs/workbench/evaluations/'

def sync(root):
    paths=list((root/PREFIX).glob('*/report.json'))
    with connection(root) as con:known={r[0]:r[1] for r in con.execute('SELECT path,signature FROM report_index')}
    updates=[];present=set()
    for path in paths:
        key=path.relative_to(root).as_posix();present.add(key);sig=json.dumps(stat_key(path))
        if known.get(key)==sig:continue
        payload=read_json(path)
        if json.dumps(stat_key(path))!=sig:continue
        updates.append((path.parent.name,key,sig,payload))
    if updates or set(known)-present:
        with connection(root) as con:
            for ident,key,sig,payload in updates:
                samples=payload.get('samples',[]);summary={k:v for k,v in payload.items() if k!='samples'}
                con.execute('INSERT OR REPLACE INTO report_index(id,path,signature,model,artifact,evaluated,payload) VALUES(?,?,?,?,?,?,?)',(ident,key,sig,payload.get('model'),payload.get('artifact'),payload.get('evaluated_at') or '',json.dumps(summary,ensure_ascii=False)))
                con.execute('DELETE FROM report_samples WHERE report=?',(ident,))
                con.executemany('INSERT INTO report_samples(report,position,image,payload) VALUES(?,?,?,?)',[(ident,i,r.get('image_id'),json.dumps(r,ensure_ascii=False)) for i,r in enumerate(samples)])
            for missing in set(known)-present:
                con.execute('DELETE FROM report_samples WHERE report IN (SELECT id FROM report_index WHERE path=?)',(missing,));con.execute('DELETE FROM report_index WHERE path=?',(missing,))

def summaries(root,model='',page=1,size=30,exclude_artifacts=()):
    sync(root)
    # Reports of permanently deleted models are hidden (files kept) without breaking totals or paging.
    hidden='(artifact IS NULL OR artifact NOT IN (SELECT value FROM json_each(?)))';hidden_values=[json.dumps(sorted(exclude_artifacts))]
    where=hidden+(' AND model=?' if model else '');values=hidden_values+([model] if model else [])
    with connection(root) as con:
        total=con.execute('SELECT COUNT(*) FROM report_index WHERE '+where,values).fetchone()[0];page=min(page,max(1,(total+size-1)//size))
        rows=con.execute('SELECT id,payload FROM report_index WHERE '+where+' ORDER BY evaluated DESC,id DESC LIMIT ? OFFSET ?',values+[size,(page-1)*size]).fetchall()
        models=[r[0] for r in con.execute('SELECT DISTINCT model FROM report_index WHERE model IS NOT NULL AND '+hidden,hidden_values)]
    return [{'report_id':r[0],**json.loads(r[1])} for r in rows],total,page,models

def samples(root,ident,page,size,image):
    sync(root)
    with connection(root) as con:
        if not con.execute('SELECT 1 FROM report_index WHERE id=?',(ident,)).fetchone():raise FileNotFoundError(ident)
        total=con.execute('SELECT COUNT(*) FROM report_samples WHERE report=?',(ident,)).fetchone()[0];page=min(page,max(1,(total+size-1)//size))
        items=[json.loads(r[0]) for r in con.execute('SELECT payload FROM report_samples WHERE report=? ORDER BY position LIMIT ? OFFSET ?',(ident,size,(page-1)*size))]
        valid=bool(con.execute('SELECT 1 FROM report_samples WHERE report=? AND image=? LIMIT 1',(ident,image)).fetchone()) if image else None
    return {'items':items,'total':total,'page':page,'size':size,'selected_image_valid':valid}
