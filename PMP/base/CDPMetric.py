import abc
from CDP.base.CDPTool import *


class CDPMetric(CDPTool):
    __metaclass__ = abc.ABCMeta

    def __init__(self, var, data1, data2):
        self.var = var
        self.data1 = data1
        self.data2 = data2

    @abc.abstractmethod
    def compute(self):
        """Compute something"""
        raise NotImplementedError()

    def __call__(self):
        self.compute()
