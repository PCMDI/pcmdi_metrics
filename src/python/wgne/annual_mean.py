import cdutil,cdms2

def compute(dm,do):
    """ Computes bias"""
    cdms2.setAutoBounds('on') # Do we really want this? Wouldn't it better to let it fails
    return cdutil.averager(dm,axis='t')-cdutil.averager(do,axis='t')
