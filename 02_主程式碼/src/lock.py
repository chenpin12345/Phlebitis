from __future__ import annotations
import os
import tempfile
from pathlib import Path
from src.common import ROOT


class OperationLock:
    """OS lock: training, standalone prediction and the LINE worker cannot share the GPU."""
    def __init__(self,path=None):
        # Shared across project copies launched by this Windows user.
        self.path=Path(path) if path else Path(tempfile.gettempdir())/'phlebitis-local-compute.lock'
        self.machine_mutex=path is None
        self.handle=None
    def __enter__(self):
        path=self.path
        path.parent.mkdir(parents=True,exist_ok=True)
        self.f=path.open("a+b")
        self.f.seek(0,os.SEEK_END)
        if self.f.tell()==0:
            self.f.write(b"0");self.f.flush()
        self.f.seek(0)
        try:
            if os.name=="nt":
                import msvcrt
                msvcrt.locking(self.f.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.f.close()
            raise RuntimeError("Training or LINE inference is already running. Stop it before starting another GPU operation.")
        if os.name=='nt' and self.machine_mutex:
            import ctypes
            from ctypes import wintypes
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.CreateMutexW.argtypes=[ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR]
            kernel.CreateMutexW.restype=wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
            kernel.ReleaseMutex.argtypes=[wintypes.HANDLE]
            kernel.CloseHandle.argtypes=[wintypes.HANDLE]
            self.kernel=kernel
            handle=kernel.CreateMutexW(None,False,'Global\\PhlebitisComputeV1')
            if not handle:
                self.__exit__();raise RuntimeError('Unable to acquire machine compute mutex; another Windows account may own it')
            state=kernel.WaitForSingleObject(handle,0)
            if state not in (0,128):
                kernel.CloseHandle(handle);self.__exit__();raise RuntimeError('Another machine-wide model computation is active')
            self.handle=handle
        return self
    def __exit__(self,*args):
        if self.handle:
            self.kernel.ReleaseMutex(self.handle);self.kernel.CloseHandle(self.handle);self.handle=None
        self.f.seek(0)
        if os.name=="nt":
            import msvcrt
            msvcrt.locking(self.f.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(self.f.fileno(),fcntl.LOCK_UN)
        self.f.close()
