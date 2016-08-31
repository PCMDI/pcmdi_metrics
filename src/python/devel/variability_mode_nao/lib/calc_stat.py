def calcBias(a, b):
  # Calculate bias
  # a, b: cdms 2d variables (lat, lon) 
  import cdutil
  result = cdutil.averager(a, axis='xy', weights='weighted') - cdutil.averager(b, axis='xy', weights='weighted')
  return result

def calcRMS(a,b):
  # Calculate root mean square (RMS) difference
  # a, b: cdms 2d variables on the same grid (lat, lon) 
  import genutil
  result = genutil.statistics.rms(a, b, axis='xy')
  return result

def calcRMSc(a,b):
  # Calculate centered root mean square (RMS) difference 
  # Reference: Taylor 2001 Journal of Geophysical Research, 106:7183-7192
  # a, b: cdms 2d variables on the same grid (lat, lon) 
  import genutil
  result = genutil.statistics.rms(a, b, axis='xy', centered=1)
  return result

def calcSCOR(a,b):
  # Calculate spatial correlation
  # a, b: cdms 2d variables on the same grid (lat, lon) 
  import genutil
  result = genutil.statistics.correlation(a, b, weights='generate', axis='xy')
  return result
 
def calcTCOR(a,b):
  # Calculate temporal correlation
  # a, b: cdms 1d variables 
  import genutil
  result = genutil.statistics.correlation(a, b)
  return result

def calcSTD(a):
  # Calculate standard deviation
  # a: cdms 1d variables 
  import genutil
  result = genutil.statistics.std(a)
  return result
