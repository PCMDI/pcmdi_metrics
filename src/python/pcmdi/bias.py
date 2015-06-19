import cdutil,cdms2
import MV2 as MV

def compute(dm,do):
    """ Computes bias"""
    if dm is None and do is None: # just want the doc
      return {
          "Name":"Bias",
          "Abstract": "Compute Full Average of Model - Observation",
          "Contact":"Peter Gleckler <gleckler1@llnl.gov>",
          }
    return MV.float(MV.average(MV.subtract(dm,do)))
