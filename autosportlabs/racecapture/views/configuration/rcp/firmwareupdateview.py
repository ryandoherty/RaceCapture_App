import kivy
kivy.require('1.8.0')

from kivy.properties import ObjectProperty
from kivy import platform
from settingsview import SettingsMappedSpinner, SettingsSwitch
from mappedspinner import MappedSpinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.app import Builder
from kivy import platform
from autosportlabs.racecapture.views.util.alertview import confirmPopup, okPopup
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.util.alertview import alertPopup
from asl_f4_loader import fw_update
from time import sleep
from threading import Thread

Builder.load_file('autosportlabs/racecapture/views/configuration/rcp/firmwareupdateview.kv')

if platform == 'win':
    RESET_DELAY = 5000
else:
    RESET_DELAY = 1000
#TODO: MK1 support
class FirmwareUpdateView(BaseConfigView):
    progress_gauge = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(FirmwareUpdateView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')

    def on_config_updated(self, rcpCfg):
        pass

    def check_online(self):
        popup = Popup(title='Check Online',
                      content=Label(text='Coming soon!'),
                      size_hint=(None, None), size=(400, 400))
        popup.open()

    def prompt_manual_restart(self):
        popup = None
        def _on_ok(*args):
            popup.dismiss()
            self._restart_json_serial()
        popup = okPopup('Operation Complete',
                        '1. Unplug RaceCapture from USB\n2. Wait 3 seconds\n3. Re-connect USB',
                        _on_ok)
        
    def prompt_manual_bootloader_mode(self, instance):
        self._popup.dismiss()
        self._teardown_json_serial()
        popup = None
        def _on_answer(inst, answer):
            popup.dismiss()
            if answer == True:
                self._start_update_fw(instance)
            else:
                self._restart_json_serial()                
        popup = confirmPopup('Enable Bootloader Mode',
                             '1. Disconnect 12v power\n2. Unplug RaceCapture from USB\n' \
                             '3. Wait 3 seconds\n4. While holding front panel button, re-connect USB',
                             _on_answer)
        
    def select_file(self):
        if platform == 'win':
            ok_cb = self.prompt_manual_bootloader_mode
        else:
            ok_cb = self._start_update_fw
        content = LoadDialog(ok=ok_cb, 
                             cancel=self.dismiss_popup,
                             filters=['*' + '.ihex'])
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def _update_progress_gauge(self, percent):
        kvFind(self, 'rcid', 'fw_progress').value = int(percent)

    def _teardown_json_serial(self):
        # It's ok if this fails, in the event of no device being present,
        # we just need to disable the com port
        self.rc_api.disable_autorecover()
        try:
            #Windows workaround (because windows sucks at enumerating
            #USB in a timely fashion)
            if not platform == 'win':
                self.rc_api.resetDevice(True, RESET_DELAY)
            self.rc_api.shutdown_comms()
        except:
            pass
        sleep(5)

    def _restart_json_serial(self):
        self.rc_api.enable_autorecover()
        self.rc_api.run_auto_detect()

    def _update_thread(self, instance):
        try:
            selection = instance.selection
            filename = selection[0] if len(selection) else None
            if filename:
                #Even though we stopped the RX thread, this is OK
                #since it doesn't return a value
                try:
                    kvFind(self, 'rcid', 'fw_progress').title="Processing"
                    self._teardown_json_serial()
                except:
                    import sys, traceback
                    print "Exception in user code:"
                    print '-'*60
                    traceback.print_exc(file=sys.stdout)
                    print '-'*60
                    pass

                kvFind(self, 'rcid', 'fw_progress').title="Progress"

                #Get our firmware updater class and register the
                #callback that will update the progress gauge
                fu = fw_update.FwUpdater()
                fu.register_progress_callback(self._update_progress_gauge)

                retries = 5
                port = None
                while retries > 0 and not port:
                    #Find our bootloader
                    port = fu.scan_for_device()

                    if not port:
                        retries -= 1
                        sleep(2)

                if not port:
                    kvFind(self, 'rcid', 'fw_progress').title=""
                    raise Exception("Unable to locate bootloader")

                #Go on our jolly way
                fu.update_firmware(filename, port)
                kvFind(self, 'rcid', 'fw_progress').title="Restarting"

                #Windows workaround
                if platform == 'win':
                    self.prompt_manual_restart()
                #Sleep for a few seconds since we need to let USB re-enumerate
                sleep(3)
            else:
                alertPopup('Error Loading', 'No firmware file selected')
        except Exception as detail:
            alertPopup('Error Loading', 'Failed to Load Firmware:\n\n' + str(detail))

        if not platform == 'win':
            self._restart_json_serial()
        kvFind(self, 'rcid', 'fw_progress').value = 0
        kvFind(self, 'rcid', 'fw_progress').title=""



    def _start_update_fw(self, instance):
        self._popup.dismiss()
        #The comma is necessary since we need to pass in a sequence of args
        t = Thread(target=self._update_thread, args=(instance,))
        t.daemon = True
        t.start()

    def dismiss_popup(self, *args):
        self._popup.dismiss()
