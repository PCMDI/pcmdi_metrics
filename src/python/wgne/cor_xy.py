import genutil

def compute(dm,do):
    """ Computes correlation"""
    return float(genutil.statistics.correlation(dm,do,axis='xy',weights='weighted'))
