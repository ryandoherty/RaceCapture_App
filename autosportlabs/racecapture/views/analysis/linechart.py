from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from installfix_garden_graph import Graph, MeshLinePlot, LinePlot
from kivy.utils import get_color_from_hex as rgb
from kivy.app import Builder

Builder.load_file('autosportlabs/racecapture/views/analysis/linechart.kv')

#DEFAULT_CHART_COLORS = ['FFFFFF', '003AC1','FF5D00','FFC700','607DC1','FFAE7F','FFE37F','919FC1','FFD6BF','FFF1BF']
#DEFAULT_CHART_COLORS = ['FFFFFF', '8A00B8', '3366FF', 'F5B800', '8AB800']
#DEFAULT_CHART_COLORS = ['5DA5DA', 'FAA43A','60BD68', 'F17CB0', 'B2912F', 'B276B2','DECF3F', 'F15854', 'FFFFFF']
DEFAULT_CHART_COLORS =  ['2b908f', '90ee7e', 'f45b5b', '7798BF', 'aaeeee', 'ff0066', 'eeaaee', '55BF3B', 'DF5353', '7798BF', 'aaeeee']

class LineChart(AnalysisWidget):
    color_index = 0
    def __init__(self, **kwargs):
        super(LineChart, self).__init__(**kwargs)        
        
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
        sample_index = 0
        for sample in samples:
            points.append((sample_index, sample[1]))
            sample_index += 1 
            
        chart.ymin = min
        chart.ymax = max
        chart.xmin = 0
        chart.xmax = sample_index
        plot.points = points
        
        
