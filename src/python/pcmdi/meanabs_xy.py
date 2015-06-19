import MV2 as MV 

def compute(dm,do):
    """ Computes Mean Absolute Error"""
    if dm is None and do is None: # just want the doc
      return {
          "Name":"Mean Absolute Error",
          "Abstract": "Compute Full Average of Absolute Difference Between Model And Observation",
          "Contact":"Peter Gleckler <gleckler1@llnl.gov>",
          }
    mae = MV.average(MV.absolute(MV.subtract(dm,do)))
    return float(mae) 

