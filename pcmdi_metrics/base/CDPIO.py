import abc


class CDPIO(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def read():
        """Read a file"""
        raise NotImplementedError()

    @abc.abstractmethod
    def write():
        """Write a file"""
        raise NotImplementedError()
