from base import BaseComponentStatusView

class LoggingStatusView(BaseComponentStatusView):

    title = 'Logging Status'
    root_status = 'logging'

    logging_definitions = ['Idle', 'Writing', 'Error']

    def __init__(self, status):
        super(LoggingStatusView, self).__init__(self.title, status)

    def render(self):

        pass

