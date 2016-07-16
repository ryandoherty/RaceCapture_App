import kivy
kivy.require('1.9.1')
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty

class DashboardScreen(AnchorLayout):
    """
    A base class to for all dashboard screens.
    """
    name = StringProperty()

    def on_enter(self):
        """
        Called when the screen is shown. 
        """
        pass
