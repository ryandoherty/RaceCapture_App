import kivy
kivy.require('1.9.0')

from math import sin
from installfix_garden_graph import Graph, LinePlot
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex as rgb
from kivy.app import Builder
from kivy.clock import Clock
from valuefield import *
from utils import *
from channelnameselectorview import ChannelNameSelectorView
from channelnamespinner import ChannelNameSpinner
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseMultiChannelConfigView, BaseChannelView
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.popup.centeredbubble import CenteredBubble, WarnLabel
from kivy.metrics import dp

ANALOG_CHANNELS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/analogchannelsview.kv'
        
class AnalogChannelsView(BaseMultiChannelConfigView):
    def __init__(self, **kwargs):
        Builder.load_file(ANALOG_CHANNELS_VIEW_KV)
        super(AnalogChannelsView, self).__init__(**kwargs)
        self.channel_title = 'Analog '
        self.accordion_item_height = dp(80)
        
            
    def channel_builder(self, index, max_sample_rate):
        editor = AnalogChannel(id='analog' + str(index), channels=self.channels)
        editor.bind(on_modified=self.on_modified)
        if self.config:
            editor.on_config_updated(self.config.channels[index], max_sample_rate)
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
                    
    def on_config_updated(self, channelConfig, max_sample_rate):
        self.ids.chan_id.setValue(channelConfig)
        self.ids.sr.setValue(channelConfig.sampleRate, max_sample_rate)

        scaling_mode = channelConfig.scalingMode

        check_raw = self.ids.smRaw
        check_linear = self.ids.smLinear
        check_mapped = self.ids.smMapped
        if scaling_mode == 0:
            check_raw.active = True
            check_linear.active = False
            check_mapped.active = False
        elif scaling_mode == 1:
            check_raw.active = False
            check_linear.active = True
            check_mapped.active = False
        elif scaling_mode == 2:
            check_raw.active = False
            check_linear.active = False
            check_mapped.active = True
        
        self.ids.linearscaling.text = str(channelConfig.linearScaling)
        map_editor = self.ids.map_editor
        map_editor.on_config_changed(channelConfig.scalingMap)
        map_editor.bind(on_map_updated=self.on_map_updated)

        self.channelConfig = channelConfig
        
    def on_map_updated(self, *args):
        self.channelConfig.stale = True
        self.dispatch('on_modified', self.channelConfig)        
        

class AnalogScaler(Graph):
    def __init__(self, **kwargs):
        super(AnalogScaler, self).__init__(**kwargs)

WARN_DISMISS_TIMEOUT = 3

class AnalogScalingMapEditor(BoxLayout):
    map_size = SCALING_MAP_POINTS
    scaling_map = None
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
        
    def on_config_changed(self, scaling_map):
        map_size = self.map_size
        self.setTabStops(map_size)
        for i in range(map_size):
            volts = scaling_map.getVolts(i)
            scaled = scaling_map.getScaled(i)
            volts_cell = kvFind(self, 'rcid', 'v_' + str(i))
            scaled_cell = kvFind(self, 'rcid', 's_' + str(i))
            self.set_volts_cell(volts_cell, volts)
            self.set_scaled_cell(scaled_cell, scaled)            
        self.scaling_map = scaling_map
        self.regen_plot()

    #TODO make regen_plot2 the actual routine; we should'nt have to delete and re-add the plot to change the points
    def regen_plot(self):
        scalingMap = self.scaling_map
        
        graphContainer = self.ids.graphcontainer
        graphContainer.clear_widgets()
        
        graph = AnalogScaler()
        graphContainer.add_widget(graph)
        
        plot = LinePlot(color=rgb('00FF00'), line_width=1.25)
        graph.add_plot(plot)
        self.plot = plot
                
        points = []
        map_size = self.map_size
        max_scaled = None
        min_scaled = None
        for i in range(map_size):
            volts = scalingMap.getVolts(i)
            scaled = scalingMap.getScaled(i)
            points.append((volts, scaled))
            if max_scaled == None or scaled > max_scaled:
                max_scaled = scaled
            if min_scaled == None or scaled < min_scaled:
                min_scaled = scaled
            
        graph.ymin = min_scaled
        graph.ymax = max_scaled
        graph.xmin = 0
        graph.xmax = 5
        plot.points = points
            
    def on_map_updated(self):
        pass
    
    def _refocus(self, widget):
        widget.focus = True
        
    def on_volts(self, mapBin, instance):
        value = instance.text.strip()
        if value == '' or value == "." or value == "-":
            value = 0
            instance.text = str(value)
        try:
            value = float(value)
            if self.scaling_map:
                self.scaling_map.setVolts(mapBin, value)
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
            original_value = self.scaling_map.getVolts(mapBin)
            self.set_volts_cell(instance, original_value)
            Clock.schedule_once(lambda dt: self._refocus(instance))
        except Exception as e:

            alertPopup('Scaling Map', str(e))
            original_value = self.scaling_map.getVolts(mapBin)
            self.set_volts_cell(instance, original_value)

    def on_scaled(self, mapBin, instance, value):
        value = value.strip()
        if value == '' or value == "." or value == "-":
            value = 0
            instance.text = str(value)
        try:
            value = float(value)
            if self.scaling_map:
                self.scaling_map.setScaled(mapBin, value)
                self.dispatch('on_map_updated')
                self.regen_plot()
        except Exception as e:
            print("Error updating chart with scaled value: " + str(e))
            
        

