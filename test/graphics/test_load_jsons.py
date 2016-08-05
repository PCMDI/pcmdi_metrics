import pcmdi_metrics
import glob
import os

files = glob.glob(os.path.expanduser("test/graphics/json/*/*.json"))
print files

J = pcmdi_metrics.pcmdi.io.JSONs(files)


data = J()
data.info()
print data.shape
print data.getAxis(4)[:]
print data.shape
data = J(region=['NHEX','SHEX','TROPICS',"global"])
print data.shape
data = J(variable=slice(2,None,2),region=['NHEX','SHEX','TROPICS',"global"])
print data.shape
