"""Bounded views for existing case/event tables; no duplicate authority."""
import json

def page_records(kind,page=1,size=30,session=''):
    from src.workbench.storage import db
    if page<1 or not 1<=size<=100:raise ValueError('無效的分頁')
    with db() as con:
        if kind=='cases':
            total=con.execute('SELECT COUNT(*) FROM cases').fetchone()[0]
            page=min(page,max(1,(total+size-1)//size))
            items=[json.loads(r[0]) for r in con.execute('SELECT data FROM cases ORDER BY id DESC LIMIT ? OFFSET ?',(size,(page-1)*size))]
            active=0
        else:
            if not isinstance(session,str) or len(session)>80:raise ValueError('無效的模擬使用者')
            total=con.execute('SELECT COUNT(*) FROM events WHERE session=?',(session,)).fetchone()[0]
            page=min(page,max(1,(total+size-1)//size))
            rows=con.execute('SELECT * FROM events WHERE session=? ORDER BY updated DESC,id DESC LIMIT ? OFFSET ?',(session,size,(page-1)*size)).fetchall()
            items=[{**dict(r),'payload':json.loads(r['payload'])} for r in reversed(rows)]
            active=con.execute("SELECT COUNT(*) FROM events WHERE session=? AND status IN ('queued','running')",(session,)).fetchone()[0]
    return {'items':items,'page':page,'size':size,'total':total,'active_count':active}
