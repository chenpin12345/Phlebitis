"""Stat-invalidated projections. Never used to authorize loading or deletion."""
import json
from src.common import read_json
from src.workbench.queries.data_index import connection, stat_key

def cached_json(path,root):
    key=str(path.relative_to(root));signature=json.dumps(stat_key(path))
    if signature=='null':raise FileNotFoundError(path)
    with connection(root) as con:
        row=con.execute('SELECT signature,payload FROM file_projection WHERE path=?',(key,)).fetchone()
    if row and row[0]==signature:return json.loads(row[1])
    value=read_json(path)
    if json.dumps(stat_key(path))!=signature:raise RuntimeError('檔案更新中，請稍後重試')
    with connection(root) as con:
        con.execute('INSERT OR REPLACE INTO file_projection(path,signature,payload) VALUES(?,?,?)',(key,signature,json.dumps(value,ensure_ascii=False,allow_nan=False)))
    return value

def cached_many(paths,root):
    """One connection per collection, not per model."""
    paths=list(paths)
    keys=[p.relative_to(root).as_posix() for p in paths]
    with connection(root) as con:
        known={}
        for start in range(0,len(keys),400):
            batch=keys[start:start+400]
            known.update({r[0]:(r[1],r[2]) for r in con.execute('SELECT path,signature,payload FROM file_projection WHERE path IN ('+','.join('?' for _ in batch)+')',batch)})
    updates=[];result=[]
    for path in paths:
        key=path.relative_to(root).as_posix();sig=json.dumps(stat_key(path));row=known.get(key)
        if row and row[0]==sig:value=json.loads(row[1])
        else:
            value=read_json(path)
            if sig!=json.dumps(stat_key(path)):raise RuntimeError('模型設定更新中')
            updates.append((key,sig,json.dumps(value,ensure_ascii=False)))
        result.append(value)
    if updates:
        with connection(root) as con:con.executemany('INSERT OR REPLACE INTO file_projection(path,signature,payload) VALUES(?,?,?)',updates)
    return result
