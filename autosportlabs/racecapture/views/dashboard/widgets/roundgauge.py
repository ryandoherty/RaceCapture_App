import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.metrics import dp
from autosportlabs.racecapture.views.dashboard.widgets.fontgraphicalgauge import FontGraphicalGauge
from utils import kvFind

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/roundgauge.kv')

class RoundGauge(FontGraphicalGauge):
    
    def __init__(self, **kwargs):
        super(RoundGauge, self).__init__(**kwargs)
        self.initWidgets()
            
    def initWidgets(self):
        self.menu_args =  dict(
                creation_direction=-1,
                radius=30,
                creation_timeout=.4,
                choices=[
                dict(text='Remove', index=1, callback=self.removeGauge),
                dict(text='Select Channel', index=2, callback=self.selectChannel),
                dict(text='Customize', index=3, callback=self.customizeGauge),
                ])

            
            
            
                
    
    def removeGauge(self, *args):
        print "remove Gauge"
        args[0].parent.dismiss()        

    def customizeGauge(self, *args):
        print "customize gauge"
        args[0].parent.dismiss()

    def selectChannel(self, *args):
        print "select channel"
        args[0].parent.dismiss()
