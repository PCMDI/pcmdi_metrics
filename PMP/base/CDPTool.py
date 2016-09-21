import abc


class CDPTool(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def compute():
        """Compute something"""
        raise NotImplementedError()
