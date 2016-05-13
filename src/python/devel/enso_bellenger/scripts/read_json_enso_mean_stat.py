import json
import string

execfile('./plot_metrics_mean_stat.py')

test = True

json_file = 'ENSO_mean_stat_cmip5_piControl_r1i1p1_mo_atm.json'
json_filename = string.split(json_file,'.')[0]

mip = string.split(json_filename,'_')[3]
exp = string.split(json_filename,'_')[4]
run = string.split(json_filename,'_')[5]
fq = string.split(json_filename,'_')[6]
realm = string.split(json_filename,'_')[7]

print mip, exp, run, fq, realm

with open(json_filename+'.json') as json_data:
  d = json.load(json_data)

mods=[]
mods = d.keys()
mods.sort()

reg_time = []
stats = d[mods[0]]['mean_stat'].keys()

for stat in stats:
  print stat
  data = [] 
  mods_stat = []
  for mod in mods:
    try:
      data.append(d[mod]['mean_stat'][stat])
      mods_stat.append(mod)
    except:
      print "No data for ", mod, stat
      continue 
  plot_metrics_mean_stat(mods_stat,data)
