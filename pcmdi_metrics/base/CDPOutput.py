import abc


class CDPOutput(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parameter):
        self.parameter = parameter

    def set_parameter(self, p):
        self.parameter = p

    def get_parameter(self):
        return self.parameter

    @abc.abstractmethod
    def check_parameter():
        """Check that parameter has the correct information
        for this kind of output."""
        raise NotImplementedError()

    @abc.abstractmethod
    def create_output():
        """Given parameters, create the respective output."""
        raise NotImplementedError()

    def run(self):
        self.check_parameter()
        self.create_output()
