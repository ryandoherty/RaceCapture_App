from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from installfix_garden_graph import Graph, MeshLinePlot
from kivy.utils import get_color_from_hex as rgb
from kivy.app import Builder

Builder.load_file('autosportlabs/racecapture/views/analysis/linechart.kv')

class LineChart(AnalysisWidget):
    def __init__(self, **kwargs):
        super(LineChart, self).__init__(**kwargs)        
        
    def add_channel_data(self, samples, min, max):
        
        chart = self.ids.chart
        
        plot = MeshLinePlot(color=rgb('00FF00'))
        chart.add_plot(plot)
        points = []
        sample_index = 0
        for sample in samples:
            points.append((sample_index, sample[1]))
            print(str(sample[1]))
            sample_index += 1 
            
        chart.ymin = min
        chart.ymax = max
        chart.xmin = 0
        chart.xmax = sample_index
        plot.points = points
        
        
