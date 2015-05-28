from kivy import platform
__all__ = ('safe_thread_exit')


if platform == 'android':
    import jnius

def safe_thread_exit():
    if platform == 'android':
        jnius.detach() #detach the current thread from pyjnius, else hard crash occurs
        