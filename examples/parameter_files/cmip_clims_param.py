import os
import glob

vars = ['pr','rlut', 'rsut','rsutcs','rlutcs','tas','prw','tauu','tauv','uas','vas','psl','hus','ta','ua','va', 'zg']
#vars = ['rlut']
var = ['rlut']
realm = 'atm'
MIP = 'cmip5'
exp = 'historical'

modpath = os.path.join('/work', 'cmip5', exp, realm, 'mo_new')


filename_template = MIP + '.*' + '.' + exp + '.r1i1p1.mo.' + realm + '.Amon.' + '*' + '.ver-*.latestX.xml'

glb = os.path.join(modpath,"rlut",filename_template)
files = glob.glob(glb)

file = files[:5]
#var= vars[:3]
climout = 'cmip5clims_newsystem_' + exp + '/'  

results_dir = climout

start = '1981'
end = '2005-12-31'

granularize = ["file", "var"]
