import kivy
kivy.require('1.9.1')
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty

class DashboardScreen(AnchorLayout):
    name = StringProperty()

    def on_enter(self):
        pass
