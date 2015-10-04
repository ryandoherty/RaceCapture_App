import kivy
kivy.require('1.9.0')
from kivy.logger import Logger
from kivy.clock import Clock
from time import sleep
from threading import Thread



"""Responsible for querying status from the RaceCapture API
"""
class StatusPump(object):
    
    #how often we query for status
    STATUS_QUERY_INTERVAL = 2.0
    
    #Connection to the RC API
    _rc_api = None
    
    #Things that care about status updates
    _listeners = []
    
    #Worker Thread
    _status_thread = None
    
    def add_listener(self, listener):
        self._listeners.append(listener)
                    
    def start(self, rc_api):
        Logger.info('StatusPump: starting')
        self._rc_api = rc_api
        self._status_thread = Thread(target=self.status_worker)
        self._status_thread.daemon = True
        self._status_thread.start()
        
    def status_worker(self):
        self._rc_api.addListener('status', self._on_status_updated)        
        while True:
            self._rc_api.get_status()
            sleep(self.STATUS_QUERY_INTERVAL)

    def _update_all_listeners(self, status):
        for listener in self._listeners:
            listener(status)
        
    def _on_status_updated(self, status):
        Clock.schedule_once(lambda dt: self._update_all_listeners(status))
