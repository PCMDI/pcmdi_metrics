import pcmdi_metrics
import glob
import os

files = glob.glob(os.path.expanduser("~/Peter/*/*.json"))
print files

J = pcmdi_metrics.pcmdi.io.JSONs(files)


print J.getAxisList()

