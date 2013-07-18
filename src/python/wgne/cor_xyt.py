import genutil

def compute(dm,do):
    """ Computes correlation"""
    return float(statistics.correlation(dm,do,axis='xyt',weights='weighted'))
