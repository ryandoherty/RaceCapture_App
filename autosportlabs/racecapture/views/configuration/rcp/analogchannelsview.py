import kivy
kivy.require('1.8.0')

from math import sin
from installfix_garden_graph import Graph, MeshLinePlot
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex as rgb
from kivy.app import Builder
from kivy.clock import Clock
from valuefield import *
from utils import *
from channels import *
from channelnameselectorview import ChannelNameSelectorView
from channelnamespinner import ChannelNameSpinner
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseMultiChannelConfigView, BaseChannelView
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.popup.centeredbubble import CenteredBubble
from kivy.metrics import dp

ANALOG_CHANNELS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/analogchannelsview.kv'
        
class AnalogChannelsView(BaseMultiChannelConfigView):
    def __init__(self, **kwargs):
        Builder.load_file(ANALOG_CHANNELS_VIEW_KV)
        super(AnalogChannelsView, self).__init__(**kwargs)
        self.channel_title = 'Analog '
        self.accordion_item_height = dp(85)
        
            
    def channel_builder(self, index):
        editor = AnalogChannel(id='analog' + str(index), channels=self.channels)
        editor.bind(on_modified=self.on_modified)
        if self.config:
            editor.on_config_updated(self.config.channels[index])
        return editor
            
    def get_specific_config(self, rcp_cfg):
        return rcp_cfg.analogConfig
        
class AnalogChannel(BaseChannelView):
    def __init__(self, **kwargs):
        super(AnalogChannel, self).__init__(**kwargs)

    def on_linear_map_value(self, instance, value):
        try:
            if self.channelConfig:
                self.channelConfig.linearScaling = float(value)
                self.channelConfig.stale = True
                self.dispatch('on_modified', self.channelConfig)
        except:
            pass
            
                    
    def on_scaling_type_raw(self, instance, value):
        if self.channelConfig and value:
            self.channelConfig.scalingMode = ANALOG_SCALING_MODE_RAW
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                        
    def on_scaling_type_linear(self, instance, value):
        if self.channelConfig and value:
            self.channelConfig.scalingMode = ANALOG_SCALING_MODE_LINEAR
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                        
    def on_scaling_type_map(self, instance, value):
        if self.channelConfig and value:
            self.channelConfig.scalingMode = ANALOG_SCALING_MODE_MAP
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                    
    def on_config_updated(self, channelConfig):
        channelSpinner = kvFind(self, 'rcid', 'chanId')
        channelSpinner.setValue(channelConfig)

        sampleRateSpinner = kvFind(self, 'rcid', 'sr')
        sampleRateSpinner.setValue(channelConfig.sampleRate)

        scalingMode = channelConfig.scalingMode

        checkRaw = kvFind(self, 'rcid','smRaw')
        checkLinear = kvFind(self, 'rcid', 'smLinear')
        checkMapped = kvFind(self, 'rcid', 'smMapped')
        if scalingMode == 0:
            checkRaw.active = True
            checkLinear.active = False
            checkMapped.active = False
        elif scalingMode == 1:
            checkRaw.active = False
            checkLinear.active = True
            checkMapped.active = False
        elif scalingMode == 2:
            checkRaw.active = False
            checkLinear.active = False
            checkMapped.active = True
        
        kvFind(self, 'rcid', 'linearscaling').text = str(channelConfig.linearScaling)
        mapEditor = kvFind(self, 'rcid', 'mapEditor')
        mapEditor.on_config_changed(channelConfig.scalingMap)
        mapEditor.bind(on_map_updated=self.on_map_updated)

        self.channelConfig = channelConfig
        
    def on_map_updated(self, *args):
        self.channelConfig.stale = True
        self.dispatch('on_modified', self.channelConfig)        
        

class AnalogScaler(Graph):
    def __init__(self, **kwargs):
        super(AnalogScaler, self).__init__(**kwargs)
    



Builder.load_string('''
<WarnLabel>
    canvas.before:
        Color:
            rgba: (1.0, 0, 0, 0.5)
        Rectangle:
            pos: self.pos
            size: self.size
            
''')

class WarnLabel(Label):
    pass


WARN_DISMISS_TIMEOUT = 3

class AnalogScalingMapEditor(BoxLayout):
    mapSize = SCALING_MAP_POINTS
    scalingMap = None
    plot = None
    def __init__(self, **kwargs):
        super(AnalogScalingMapEditor, self).__init__(**kwargs)
        self.register_event_type('on_map_updated')

    def setTabStops(self, mapSize):
        voltsCellFirst = kvFind(self, 'rcid', 'v_0')
        voltsCellNext = None
        for i in range(mapSize):
            voltsCell = kvFind(self, 'rcid', 'v_' + str(i))
            scaledCell = kvFind(self, 'rcid', 's_' + str(i))
            voltsCell.set_next(scaledCell)
            if (i < mapSize - 1):
                voltsCellNext = kvFind(self, 'rcid', 'v_' + str(i + 1))
            else:
                voltsCellNext = voltsCellFirst
            scaledCell.set_next(voltsCellNext)

    def set_volts_cell(self, cell_field, value):
        cell_field.text = '{:.3g}'.format(value)
        
    def set_scaled_cell(self, scaled_field, value):
        scaled_field.text = '{:.3g}'.format(value)
        
    def on_config_changed(self, scalingMap):
        editor = kvFind(self, 'rcid', 'mapEditor')
        mapSize = self.mapSize
        self.setTabStops(mapSize)
        for i in range(mapSize):
            volts = scalingMap.getVolts(i)
            scaled = scalingMap.getScaled(i)
            voltsCell = kvFind(editor, 'rcid', 'v_' + str(i))
            scaledCell = kvFind(editor, 'rcid', 's_' + str(i))
            self.set_volts_cell(voltsCell, volts)
            self.set_scaled_cell(scaledCell, scaled)            
        self.scalingMap = scalingMap
        self.regen_plot()

    #TODO make regen_plot2 the actual routine; we should'nt have to delete and re-add the plot to change the points
    def regen_plot(self):
        scalingMap = self.scalingMap
        
        graphContainer = kvFind(self, 'rcid', 'graphcontainer')
        graphContainer.clear_widgets()
        
        graph = AnalogScaler()
        graphContainer.add_widget(graph)
        
        plot = MeshLinePlot(color=rgb('00FF00'))
        graph.add_plot(plot)
        self.plot = plot
                
        points = []
        mapSize = self.mapSize
        maxScaled = None
        minScaled = None
        for i in range(mapSize):
            volts = scalingMap.getVolts(i)
            scaled = scalingMap.getScaled(i)
            points.append((volts, scaled))
            if maxScaled == None or scaled > maxScaled:
                maxScaled = scaled
            if minScaled == None or scaled < minScaled:
                minScaled = scaled
            
        graph.ymin = minScaled
        graph.ymax = maxScaled
        graph.xmin = 0
        graph.xmax = 5
        plot.points = points
        
        
    def regen_plot2(self):
        scalingMap = self.scalingMap
        graph = kvFind(self, 'rcid', 'scalingGraph')
        
        plot = self.plot
        if not plot:
            plot = MeshLinePlot(color=rgb('FF0000'))
            graph.add_plot(plot)
            self.plot = plot
                
        points = []
        mapSize = self.mapSize
        maxScaled = None
        minScaled = None
        for i in range(mapSize):
            volts = scalingMap.getVolts(i)
            scaled = scalingMap.getScaled(i)
            points.append((volts, scaled))
            if maxScaled == None or scaled > maxScaled:
                maxScaled = scaled
            if minScaled == None or scaled < minScaled:
                minScaled = scaled
            
        graph.ymin = minScaled
        graph.ymax = maxScaled
        graph.xmin = 0
        graph.xmax = 5
        plot.points = points
            
    def on_map_updated(self):
        pass
    
    def _refocus(self, widget):
        widget.focus = True
        
    def on_volts(self, mapBin, instance, focus_value):
        if not focus_value:
            value = instance.text.strip()
            if value == '' or value == "." or value == "-": value = 0
            try:
                value = float(value)
                if self.scalingMap:
                    self.scalingMap.setVolts(mapBin, value)
                    self.dispatch('on_map_updated')
                    self.regen_plot()
            except ScalingMapException as e:
                warn = CenteredBubble()
                warn.add_widget(WarnLabel(text=str(e)))
                warn.auto_dismiss_timeout(WARN_DISMISS_TIMEOUT)
                warn.background_color = (1, 0, 0, 1.0)
                warn.size = (dp(200), dp(50))
                warn.size_hint = (None,None)
                self.get_root_window().add_widget(warn)
                warn.center_on(instance)
                original_value = self.scalingMap.getVolts(mapBin)
                self.set_volts_cell(instance, original_value)
                Clock.schedule_once(lambda dt: self._refocus(instance))
            except Exception as e:
                
                alertPopup('Scaling Map', str(e))
                original_value = self.scalingMap.getVolts(mapBin)
                self.set_volts_cell(instance, original_value)
                    
    def on_scaled(self, mapBin, instance, value):
        try:
            value = float(value)
            if self.scalingMap:
                self.scalingMap.setScaled(mapBin, value)
                self.dispatch('on_map_updated')
                self.regen_plot()
        except Exception as e:
            print("Error updating chart with scaled value: " + str(e))
            
        

