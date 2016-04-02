import kivy
kivy.require('1.9.1')

from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.app import Builder
from kivy.utils import platform
from os.path import dirname, expanduser, sep
from utils import kvFind

Builder.load_file('autosportlabs/racecapture/views/file/savedialogview.kv')

class SaveDialog(FloatLayout):
    def __init__(self, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)
        ok = kwargs.get('ok', None)
        cancel = kwargs.get('cancel', None)
        user_path = kwargs.get('user_path', '.')
            
        browser = kvFind(self, 'rcid', 'browser')
        browser.path = user_path
        browser.filters = kwargs.get('filters', ['*'])
        if ok: browser.bind(on_success = ok)
        if cancel: browser.bind(on_canceled = cancel)
