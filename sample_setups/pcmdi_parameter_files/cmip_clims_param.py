import os
import glob

realm = 'atm'
MIP = 'cmip5'
exp = 'historical'

modpath = os.path.join('/work', 'cmip5-test', exp, realm, 'mo')

filename_template = "%(variable)/cmip5.%(model).%(experiment).r1i1p1.mo.atm.Amon.%(variable).ver-%(version).latestX.xml"

variable= 'rlut'
climout = './example_results/%(variable)/%(model)/'

results_dir = climout
model = "CNRM-CM5-2"
start = '1981'
end = '2005-12-31'
num_workers = 3
granularize = ["variable", "model"]
