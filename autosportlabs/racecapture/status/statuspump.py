import kivy
kivy.require('1.9.1')
from kivy.logger import Logger
from kivy.clock import Clock
from time import sleep
from threading import Thread, Event



"""Responsible for querying status from the RaceCapture API
"""
class StatusPump(object):

    # how often we query for status
    STATUS_QUERY_INTERVAL = 2.0

    # Connection to the RC API
    _rc_api = None

    # Things that care about status updates
    _listeners = []

    # Worker Thread
    _status_thread = None

    # signals if thread should continue running
    _running = Event()

    def add_listener(self, listener):
        self._listeners.append(listener)

    def start(self, rc_api):
        if self._status_thread is not None and \
           self._status_thread.is_alive():
            Logger.info('StatusPump: Already running')
            return

        self._rc_api = rc_api
        t = Thread(target=self.status_worker)
        self._running.set()
        t.start()
        self._status_thread = t

    def stop(self):
        self._running.clear()
        try:
            self._status_thread.join()
        except Exception as e:
            Logger.warn('StatusPump: failed to join status_worker: {}'.format(e))

    def status_worker(self):
        Logger.info('StatusPump: status_worker starting')
        self._rc_api.addListener('status', self._on_status_updated)
        while self._running.is_set():
            self._rc_api.get_status()
            sleep(self.STATUS_QUERY_INTERVAL)
        Logger.info('StatusPump: status_worker exiting')

    def _update_all_listeners(self, status):
        for listener in self._listeners:
            listener(status)

    def _on_status_updated(self, status):
        Clock.schedule_once(lambda dt: self._update_all_listeners(status))
