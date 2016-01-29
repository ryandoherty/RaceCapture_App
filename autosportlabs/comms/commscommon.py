class ChainableException(Exception):
    def __init__(self, cause=None):
        m = ''

        if cause is not None:
            m += 'caused by %s' % repr(cause)
            m.strip()

        super(Exception, self).__init__(m)
        self.cause = cause

    def get_cause(self):
        return self.cause


class PortNotOpenException(ChainableException):
    pass

class CommsErrorException(ChainableException):
    pass
