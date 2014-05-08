import kivy
from math import sin
kivy.require('1.8.0')

from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.properties import NumericProperty

from utils import *

Builder.load_file('chartview.kv')

class TestGraph(Graph):
    def __init__(self, **kwargs):
        super(TestGraph, self).__init__(**kwargs)

            
class ChartView(BoxLayout):
    dataPoints = NumericProperty(0)
    actualData = MeshLinePlot(color=[1, 0, 0, 1])
    def __init__(self, **kwargs):
        super(ChartView, self).__init__(**kwargs)
        
    def add_test_data(self):
        myChart = kvFind(self, 'rcid', 'testGraph')
        #myChart.remove_plot(self.actualData)
        self.dataPoints += 1000
        self.actualData.points = [(x, sin(x / 100.)) for x in xrange(0, self.dataPoints)]
        myChart.add_plot(self.actualData)
        myChart.xmax = self.dataPoints
