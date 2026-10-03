"""Bounded incremental line cache. Truncation/replacement resets the parser."""
import threading
from collections import OrderedDict
from src.workbench.queries.data_index import stat_key

_cache=OrderedDict()
_lock=threading.Lock()

def lines(path):
    with _lock:
        sig=stat_key(path)
        if sig is None:return []
        key=str(path);entry=_cache.get(key)
        if not entry or sig[:2]!=entry['sig'][:2] or sig[2]<entry['offset'] or (sig[2]==entry['offset'] and sig!=entry['sig']):
            entry={'sig':sig,'offset':0,'partial':b'','lines':[]}
        if sig!=entry['sig'] or not entry['offset']:
            with path.open('rb') as stream:
                stream.seek(entry['offset']);chunk=stream.read();entry['offset']=stream.tell()
            pieces=(entry['partial']+chunk).split(b'\n');entry['partial']=pieces.pop()
            entry['lines'].extend(p.decode('utf-8-sig',errors='replace').rstrip('\r') for p in pieces)
            entry['sig']=sig
        _cache[key]=entry;_cache.move_to_end(key)
        while len(_cache)>32:_cache.popitem(last=False)
        return list(entry['lines'])
