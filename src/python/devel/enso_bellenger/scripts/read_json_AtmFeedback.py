import json
import string

execfile('./plot_metrics_AtmFeedback.py')

test = True

json_file = 'AtmFeedback_cmip5_piControl_r1i1p1_mo_atm_ts.json'
json_filename = string.split(json_file,'.')[0]

mip = string.split(json_filename,'_')[1]
exp = string.split(json_filename,'_')[2]
run = string.split(json_filename,'_')[3]
fq = string.split(json_filename,'_')[4]
realm = string.split(json_filename,'_')[5]
var = string.split(json_filename,'_')[6]

print mip, exp, run, fq, realm, var

with open(json_filename+'.json') as json_data:
  d = json.load(json_data)

stdv={}
mods=[]

mods = d.keys()
mods.sort()

reg_time = []
tmp = []
for mod in mods:
  reg_time.append(d[mod]['reg_time'])
  tmp.append(d[mod]['slope'])
  stdv = tmp[:]
plot_metrics_AtmFeedback(mods)
