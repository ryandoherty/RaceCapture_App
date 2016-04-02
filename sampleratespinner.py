import kivy
kivy.require('1.9.1')
from mappedspinner import MappedSpinner

class SampleRateSpinner(MappedSpinner):
    all_sample_rates = {0:'Disabled', 1:'1 Hz', 5:'5 Hz', 10:'10 Hz', 25:'25 Hz', 50:'50 Hz', 100:'100 Hz', 200:'200 Hz', 500:'500 Hz', 1000:'1000 Hz'}
    
    def __init__(self, **kwargs):
        super(SampleRateSpinner, self).__init__(**kwargs)

    def set_max_rate(self, max):
        rates = dict((k, v) for k, v in self.all_sample_rates.items() if k <= max)
        self.setValueMap(rates, 'Disabled')
