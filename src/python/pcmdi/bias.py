import MV2
import cdutil

def compute(dm, do):
    """ Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "Peter Gleckler <gleckler1@llnl.gov>",
        }
    dif = MV2.subtract(dm, do)
    return MV2.float(cdutil.averager(dif,axis='xy',weights='weighted'))
#   return MV2.float(MV2.average(MV2.subtract(dm, do))) depricated - does not use area weights
