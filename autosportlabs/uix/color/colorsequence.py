from kivy.utils import get_color_from_hex as rgb

#DEFAULT_COLOR_SEQUENCE = ['FFFFFF', '003AC1','FF5D00','FFC700','607DC1','FFAE7F','FFE37F','919FC1','FFD6BF','FFF1BF']
DEFAULT_COLOR_SEQUENCE = ['FFFFFF', '8A00B8', '3366FF', 'F5B800', '8AB800']
#DEFAULT_COLOR_SEQUENCE = ['FFFFFF', '5DA5DA', 'FAA43A','60BD68', 'F17CB0', 'B2912F', 'B276B2','DECF3F', 'F15854', 'FFFFFF']
#DEFAULT_COLOR_SEQUENCE =  ['2b908f', '90ee7e', 'f45b5b', '7798BF', 'aaeeee', 'ff0066', 'eeaaee', '55BF3B', 'DF5353', '7798BF', 'aaeeee']

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
        
        