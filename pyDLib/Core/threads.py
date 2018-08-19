# coding: utf-8
"""Define dummy threads, and integration of QtThread"""

from . import StructureError,ConnexionError

def init_threads(t=None, s=None):
    """Should define dummyThread class and dummySignal class"""
    global THREAD, SIGNAL
    THREAD = t or dummyThread
    SIGNAL = s or dummySignal



class dummyThread:
    """Thread like object. Should be replace by QThread (or an alternative)"""

    def run(self):
        pass

    def wait(self):
        pass

    def start(self):
        self.run()


class dummySignal:
    """Signal like object (with only of callback support). Should be replace by pyqtSignal"""

    def __init__(self, *args):
        self.callback = None

    def emit(self, *arg):
        if self.callback:
            self.callback(*arg)

    def connect(self, f):
        self.callback = f


def worker(func, on_error, on_done, connect_start=True):
    class C(THREAD):
        """We must subclass QThread"""

        error = SIGNAL(str)
        done = SIGNAL(object)

        def __del__(self):
            self.wait()

        def run(self):
            try:
                r = func()
            except (ConnexionError, StructureError) as e:
                self.error.emit(str(e))
            else:
                self.done.emit(r)

    th = C()
    if connect_start:
        th.error.connect(on_error)
        th.done.connect(on_done)
        th.start()
    return th


def thread_with_callback(on_error, on_done, requete_with_callback):
    """
    Return a thread emiting `state_changed` between each sub-requests.

    :param on_error: callback str -> None
    :param on_done: callback object -> None
    :param requete_with_callback: Job to execute. monitor_callable -> None
    :return: Non started thread
    """

    class C(THREAD):

        error = SIGNAL(str)
        done = SIGNAL(object)
        state_changed = SIGNAL(int, int)

        def __del__(self):
            self.wait()

        def run(self):
            try:
                r = requete_with_callback(self.state_changed.emit)
            except (ConnexionError, StructureError) as e:
                self.error.emit(str(e))
            else:
                self.done.emit(r)

    th = C()
    th.error.connect(on_error)
    th.done.connect(on_done)
    return th
