import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.anchorlayout import AnchorLayout
from iconbutton import IconButton

Builder.load_file('autosportlabs/racecapture/views/analysis/analysiswidget.kv')

class AnalysisWidget(AnchorLayout):
    def __init__(self, **kwargs):
        super(AnalysisWidget, self).__init__(**kwargs)
#        self.ids.options.on_press = self.on_options
        #self._init_view()
        
    def on_options(self, *args):
        print("on options")
        
    def _init_view(self):
        options_button=IconButton(text='|', id='options', on_press=self.on_options)
        self.add_widget(options_button)
        
    
    