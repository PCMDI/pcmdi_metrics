import cdutil,cdms2
import MV2 as MV

def compute(dm,do):
    """ Computes bias"""
    return MV.float(MV.average(MV.subtract(dm,do)))
