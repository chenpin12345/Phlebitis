"""Allowlisted file inventory and handle-bound Windows deletion.

Never follows links and never performs recursive directory deletion.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat


def boundary(path, root):
    path, root = Path(path).absolute(), Path(root).absolute()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('檔案不在核准的資源目錄內')
    # Check every existing ancestor, including project/root ancestors.
    for p in [*reversed(path.parents), path]:
        try: s = p.lstat()
        except FileNotFoundError:
            if p == path: raise
            raise ValueError('必要父目錄不存在')
        if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
            raise ValueError('符號連結／junction／reparse point 不可清理')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('解析後路徑超出核准範圍')
    return path


@contextmanager
def opened(path, root, delete=False):
    path = boundary(path, root)
    if os.name != 'nt':
        if delete: raise ValueError('此平台尚未驗證安全刪除能力')
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(fd, 'rb') as stream: yield stream, None
        return
    import ctypes
    import msvcrt
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.SetFileInformationByHandle.argtypes = [wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
    kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE,ctypes.c_void_p]
    invalid = ctypes.c_void_p(-1).value
    parents = []
    handle = None
    try:
        # Deny directory rename/delete while checking and removing the leaf.
        for parent in reversed(path.parents):
            h = kernel.CreateFileW(str(parent),0x80,3,None,3,0x02000000 | 0x00200000,None)
            if h == invalid: raise ctypes.WinError(ctypes.get_last_error())
            parents.append(h)
            buffer = ctypes.create_string_buffer(52)
            if not kernel.GetFileInformationByHandle(h,buffer): raise ctypes.WinError(ctypes.get_last_error())
            if int.from_bytes(buffer.raw[:4],'little') & 0x400: raise ValueError('父目錄已變更為 reparse point')
        handle = kernel.CreateFileW(str(path),0x80000000 | (0x10000 if delete else 0),1,None,3,0x00200000,None)
        if handle == invalid: handle=None; raise ctypes.WinError(ctypes.get_last_error())
        fd = msvcrt.open_osfhandle(handle,os.O_RDONLY | os.O_BINARY)
        handle = None  # ownership transferred to fd
        with os.fdopen(fd,'rb') as stream:
            s = os.fstat(stream.fileno())
            if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or getattr(s,'st_file_attributes',0) & 0x400:
                raise ValueError('不是獨占的一般檔案；硬連結與 reparse point 不可清理')
            def remove():
                disposition = wintypes.BOOL(True)
                if not kernel.SetFileInformationByHandle(msvcrt.get_osfhandle(stream.fileno()),4,ctypes.byref(disposition),ctypes.sizeof(disposition)):
                    raise ctypes.WinError(ctypes.get_last_error())
            yield stream, remove
    finally:
        if handle is not None: kernel.CloseHandle(handle)
        for h in reversed(parents): kernel.CloseHandle(h)


def identity(stream):
    s = os.fstat(stream.fileno())
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
        raise ValueError('檔案有硬連結或無法確認獨占歸屬')
    sha = hashlib.sha256()
    while chunk := stream.read(1024*1024): sha.update(chunk)
    return {'device':s.st_dev,'inode':s.st_ino,'bytes':s.st_size,'modified_ns':s.st_mtime_ns,'sha256':sha.hexdigest()}


def inspect(path, root):
    with opened(path,root) as (stream,_): return identity(stream)


def remove_verified(path, root, expected, before_remove):
    with opened(path,root,delete=True) as (stream,remove):
        if identity(stream) != expected: raise ValueError('檔案內容或身分已變更，停止此項清理')
        before_remove()  # durable intent before an irreversible filesystem action
        remove()


def walk(root):
    """List leaves without following any directory links; report unknowns explicitly."""
    root = Path(root)
    if not root.exists(): return
    pending = [root]
    while pending:
        base = pending.pop()
        if base != root: boundary(base,root)
        elif base.is_symlink() or getattr(base.lstat(),'st_file_attributes',0) & 0x400:
            raise ValueError('資源目錄為連結，無法確認安全範圍')
        with os.scandir(base) as entries:
            for e in entries:
                s = e.stat(follow_symlinks=False)
                if e.is_symlink() or getattr(s,'st_file_attributes',0) & 0x400:
                    yield Path(e.path), '連結／reparse point：保留，需先解除'
                elif e.is_dir(follow_symlinks=False): pending.append(Path(e.path))
                else: yield Path(e.path), None
