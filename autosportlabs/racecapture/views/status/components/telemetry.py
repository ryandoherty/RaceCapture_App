from base import BaseComponentStatusView

class TelemetryStatusView(BaseComponentStatusView):

    def __init__(self, **kwargs):
        super(TelemetryStatusView, self).__init__(**kwargs)
