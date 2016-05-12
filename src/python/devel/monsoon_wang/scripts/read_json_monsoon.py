import json
import string

execfile('./plot_metrics_monsoon.py')
execfile('./plot_scatter_monsoon.py')

#test = True
test = False

json_file = 'MPI_cmip5_historical.json'
json_filename = string.split(json_file,'.')[0]

mip = string.split(json_filename,'_')[1]
exp = string.split(json_filename,'_')[2]

print mip, exp

with open(json_filename+'.json') as json_data:
  d = json.load(json_data)

mods=[]
mods = d.keys()
mods.sort()

regs = d[mods[0]].keys()

if test:
  regs = regs[0:1]

for reg in regs:
  print reg
  data1 = [] 
  data2 = [] 
  mods_reg = []
  for mod in mods:
    try:
      data1.append(d[mod][reg]['cor'])
      data2.append(d[mod][reg]['rmsn'])
      mods_reg.append(mod)
    except:
      print "No data for ", mod, reg
      continue 
  #plot_metrics_monsoon(mods_reg,reg,data1,'cor')
  #plot_metrics_monsoon(mods_reg,reg,data2,'rmsn')
  plot_scatter_monsoon(mods_reg,reg,data1,data2)
