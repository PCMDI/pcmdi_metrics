from __future__ import print_function

import abc

from six import with_metaclass


class CDPIO(with_metaclass(abc.ABCMeta, object)):
    @abc.abstractmethod
    def read(self):
        """Read a file."""
        raise NotImplementedError()

    @abc.abstractmethod
    def write(self):
        """Write a file."""
        raise NotImplementedError()
