from base import BaseComponentStatusView

class SystemStatusView(BaseComponentStatusView):

    def __init__(self, **kwargs):
        super(SystemStatusView, self).__init__(**kwargs)
