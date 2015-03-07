from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from installfix_garden_graph import Graph, MeshLinePlot, LinePlot
from kivy.utils import get_color_from_hex as rgb
from kivy.app import Builder
from kivy.core.window import Window
Builder.load_file('autosportlabs/racecapture/views/analysis/linechart.kv')

#DEFAULT_CHART_COLORS = ['FFFFFF', '003AC1','FF5D00','FFC700','607DC1','FFAE7F','FFE37F','919FC1','FFD6BF','FFF1BF']
#DEFAULT_CHART_COLORS = ['FFFFFF', '8A00B8', '3366FF', 'F5B800', '8AB800']
#DEFAULT_CHART_COLORS = ['5DA5DA', 'FAA43A','60BD68', 'F17CB0', 'B2912F', 'B276B2','DECF3F', 'F15854', 'FFFFFF']
DEFAULT_CHART_COLORS =  ['2b908f', '90ee7e', 'f45b5b', '7798BF', 'aaeeee', 'ff0066', 'eeaaee', '55BF3B', 'DF5353', '7798BF', 'aaeeee']

class LineChart(AnalysisWidget):
    color_index = 0
    def __init__(self, **kwargs):
        super(LineChart, self).__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
    
    def _get_next_line_color(self):
        index = self.color_index
        color = rgb(DEFAULT_CHART_COLORS[index])
        index = index + 1 if index < len(DEFAULT_CHART_COLORS) - 1 else 0
        self.color_index = index
        return color
        
    def add_channel_data(self, samples, min, max):
        
        chart = self.ids.chart
        
        plot = LinePlot(color=self._get_next_line_color(), line_width=1.25)
        
        chart.add_plot(plot)
        points = []
        max_distance = 0
        sample_index = 0
        for sample in samples:
            distance = sample[1]
            if distance > max_distance:
                max_distance = distance 
            points.append((distance, sample[2]))
            sample_index += 1 
            
        chart.ymin = min
        chart.ymax = max
        chart.xmin = 0
        chart.xmax = max_distance
        plot.points = points
    
    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            button = touch.button
            scroll_dir = 0
            if touch.is_mouse_scrolling:
                if 'down' in button or 'left' in button:
                    scroll_dir = 1
                if 'up' in button or 'right' in button:
                    scroll_dir = -1
                print(str(touch) + ' ' + str(scroll_dir))
        super(LineChart, self).on_touch_down(touch)
        return False
        
        
    def on_touch_move(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        print(str(touch))
        
    def on_mouse_pos(self, x, pos):
        if not self.collide_point(pos[0], pos[1]):
            return False
        
        print(str(pos))
        
