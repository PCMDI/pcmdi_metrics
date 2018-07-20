import os
import glob

realm = 'atm'
MIP = 'cmip5'
exp = 'historical'

modpath = os.path.join('/work', 'cmip5-test', exp, realm, 'mo')

filename_template = "%(variable)/cmip5.%(model).%(experiment).r1i1p1.mo.atm.Amon.%(variable).ver-%(version).latestX.xml"

var= ['rlut', 'pr']
climout = './example_results'

results_dir = climout
model = ["BNU-ESM", "CNRM-CM5-2", "CNRM-CM5"]
start = '1981'
end = '2005-12-31'
num_workers = 3
granularize = ["var", "model"]