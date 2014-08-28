import genutil

def compute(dm,do):
    """ Computes rms """
    return float(genutil.statistics.rms(dm,do,axis='xyt',weights='weighted'))
