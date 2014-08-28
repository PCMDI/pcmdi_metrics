import MV2 as MV 

def compute(dm,do):
    """ Computes Mean Absolute Error"""
    mae = MV.average(MV.absolute(MV.subtract(dm,do)))
    return float(mae) 

