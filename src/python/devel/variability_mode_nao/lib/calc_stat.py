import cdutil
import genutil

def calcBias(a, b):
  # Calculate bias
  # a, b: cdms 2d variables (lat, lon) 
  result = cdutil.averager(a, axis='xy', weights='weighted') - cdutil.averager(b, axis='xy', weights='weighted')
  return result

def calcRMS(a,b):
  # Calculate root mean square (RMS) difference
  # a, b: cdms 2d variables on the same grid (lat, lon) 
  result = genutil.statistics.rms(a, b, axis='xy', weights='weighted')
  return result

def calcRMSc(a,b):
  # Calculate centered root mean square (RMS) difference 
  # Reference: Taylor 2001 Journal of Geophysical Research, 106:7183-7192
  # a, b: cdms 2d variables on the same grid (lat, lon) 
  result = genutil.statistics.rms(a, b, axis='xy', centered=1, weights='weighted')
  return result

def calcSCOR(a,b):
  # Calculate spatial correlation
  # a, b: cdms 2d variables on the same grid (lat, lon) 
  result = genutil.statistics.correlation(a, b, weights='generate', axis='xy')
  return result
 
def calcTCOR(a,b):
  # Calculate temporal correlation
  # a, b: cdms 1d variables 
  result = genutil.statistics.correlation(a, b)
  return result

def calcSTD(a):
  # Calculate standard deviation
  # a: cdms 1d variables 
  result = genutil.statistics.std(a, biased=0) # biased=0 option enables divided by N-1 instead of N
  return result

def calcSTDmap(a):
  # Calculate spatial standard deviation from 2D map field
  # a: cdms 2d (xy) variables
  wts = cdutil.area_weights(a)
  std = genutil.statistics.std(a, axis='xy', weights=wts)
  return std
