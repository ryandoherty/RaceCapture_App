import kivy
from math import sin
kivy.require('1.8.0')

from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.properties import NumericProperty
from random import random

from utils import *

Builder.load_file('chartview.kv')

class ChartView(BoxLayout):
    dataPoints = NumericProperty(0)
    zoomLevel = NumericProperty(100)
    scrollLevel = NumericProperty(0)
    dataPlot = MeshLinePlot(color=[1, 0, 0, 1])
    def __init__(self, **kwargs):
        super(ChartView, self).__init__(**kwargs)
        myChart = kvFind(self, 'rcid', 'testGraph')
        self.add_test_data()
        myChart.add_plot(self.dataPlot)
        
    def add_test_data(self):
        myChart = kvFind(self, 'rcid', 'testGraph')
        self.dataPoints += 1000
        self.dataPlot.points = [(x, random() - random() + sin(x / 100.)) for x in xrange(0, self.dataPoints)]
        myChart.xmax = self.dataPoints

    def zoom(self, howFar):
        myChart = kvFind(self, 'rcid', 'testGraph')
        self.zoomLevel = int(howFar)
        myChart.xmax = myChart.xmin + self.zoomLevel

    def scroll(self, howFar):
        myChart = kvFind(self, 'rcid', 'testGraph')
        self.scrollLevel = int(howFar)
        myChart.xmin = self.scrollLevel
        myChart.xmax = self.scrollLevel + self.zoomLevel
