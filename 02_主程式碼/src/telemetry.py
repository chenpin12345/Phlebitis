"""Request-local timings, without paths, payloads, credentials, or image data."""
from contextvars import ContextVar
from contextlib import contextmanager
from functools import wraps
from time import perf_counter

current=ContextVar('request_metrics',default=None)

@contextmanager
def measure(name):
    started=perf_counter()
    try:yield
    finally:
        values=current.get()
        if values is not None:
            metric=values.setdefault(name,{'ms':0,'calls':0});metric['ms']+=(perf_counter()-started)*1000;metric['calls']+=1

def timed(name):
    def decorate(fn):
        @wraps(fn)
        def call(*args,**kwargs):
            with measure(name):return fn(*args,**kwargs)
        return call
    return decorate
