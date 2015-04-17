from base import BaseComponentStatusView

class LoggingStatusView(BaseComponentStatusView):

    def __init__(self, **kwargs):
        super(LoggingStatusView, self).__init__(**kwargs)
