from kivy.utils import get_color_from_hex as rgb

DEFAULT_COLOR_SEQUENCE = ['FFFFFF', '8A00B8', '3366FF', 'F5B800', '8AB800', 'f45b5b', 'ff0066']

class ColorSequence(object):
    color_index = 0
    colors = []
    color_map = {}

    def __init__(self, colors=DEFAULT_COLOR_SEQUENCE):
        self.colors = colors

    def get_color(self, key):
        color = self.color_map.get(key)
        if not color:
            index = self.color_index
            color = rgb(self.colors[index])
            index = index + 1 if index < len(self.colors) - 1 else 0
            self.color_index = index
            self.color_map[key] = color
        return color
        
        