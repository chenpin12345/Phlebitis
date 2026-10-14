"""Private, disposable image conversion cache; source access is always rechecked."""
import io
import os
import threading
import time
from PIL import Image,ImageOps
from src.common import inside,sha256
from src.telemetry import timed
from src.workbench.storage import digest,file_lock
from src.workbench.queries.data_index import stat_key
from src.workbench.managed_files import boundary
from contextlib import contextmanager

_slots=threading.BoundedSemaphore(2)
LIMIT=1024**3
_guard=threading.Lock()
_pending={}

@contextmanager
def conversion(key):
    with _guard:
        entry=_pending.setdefault(key,[threading.Lock(),0]);entry[1]+=1
    try:
        with entry[0]:yield
    finally:
        with _guard:
            entry[1]-=1
            if not entry[1]:_pending.pop(key,None)

@timed('image')
def render(root,row,thumbnail=False):
    source=boundary(root/row['image_path'],root)
    # Refuse missing/linked sources before considering any cache entry.
    for part in [source,*source.parents]:
        if part==root.parent:break
        if part.is_symlink() or getattr(part,'is_junction',lambda:False)():raise ValueError('圖片來源不能是連結')
    signature=stat_key(source)
    if signature is None:raise FileNotFoundError(source)
    key=digest({'hash':row['sha256'],'revision':digest(row),'stat':signature,'edge':320 if thumbnail else 1800,'transform':'exif-rgb-jpeg90-v1'})
    folder=root/'runtime/cache/images';folder.mkdir(parents=True,exist_ok=True);boundary(folder,root);target=folder/(key+'.jpg')
    if target.is_file():
        boundary(target,root)
        content=target.read_bytes();os.utime(target,None);return content
    with conversion((str(root),key)),_slots:
        if target.is_file():return boundary(target,root).read_bytes()
        if sha256(source)!=row['sha256']:raise ValueError('圖片內容已變更，請先執行完整檢查')
        with Image.open(source) as original:
            image=ImageOps.exif_transpose(original).convert('RGB');image.thumbnail((320,320) if thumbnail else (1800,1800))
            stream=io.BytesIO();image.save(stream,'JPEG',quality=90);content=stream.getvalue()
        if stat_key(source)!=signature:raise RuntimeError('圖片處理期間來源變更')
        temp=folder/(key+'.'+str(os.getpid())+'.'+str(threading.get_ident())+'.tmp');temp.write_bytes(content);os.replace(temp,target)
        try:
            with file_lock(root/'runtime/image-cache.lock'):
                entries=sorted(((p.stat().st_mtime,p.stat().st_size,p) for p in folder.glob('*.jpg')),key=lambda x:x[0]);total=sum(x[1] for x in entries)
                for _,size,path in entries:
                    if total<=LIMIT:break
                    if path!=target:path.unlink(missing_ok=True);total-=size
        except (RuntimeError,PermissionError):pass
        return content

def clear(root):
    # Only generated cache entries; never traverse source data or links.
    folder=root/'runtime/cache/images'
    if not folder.exists():return
    boundary(folder,root)
    if folder.is_symlink() or getattr(folder,'is_junction',lambda:False)():raise ValueError('快取目錄不能是連結')
    for path in folder.glob('*.jpg'):
        if path.is_file() and not path.is_symlink():
            try:path.unlink()
            except PermissionError:pass
