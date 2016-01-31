from threading import RLock
from kivy import platform
__all__ = ('safe_thread_exit')


if platform == 'android':
    import jnius

def safe_thread_exit():
    if platform == 'android':
        jnius.detach()  # detach the current thread from pyjnius, else hard crash occurs


class ThreadSafeDict(dict) :
    def __init__(self, * p_arg, ** n_arg) :
        dict.__init__(self, * p_arg, ** n_arg)
        self._lock = RLock()

    def __enter__(self) :
        self._lock.acquire()
        return self

    def __exit__(self, type, value, traceback) :
        self._lock.release()
