import json

execfile('./plot_metrics.py')

with open('test_ENSO_cmip5_piControl.json') as json_data:
    d = json.load(json_data)
    #print(d)

stdv={}
mods=[]

regs = ['Nino3', 'Nino4']
#regs = ['Nino3']
for reg in regs:
  mods = d.keys()
  mods.sort()
  tmp = []
  for mod in mods:
    tmp.append(d[mod][reg]['std'])
  stdv[reg] = tmp[:]
  plot_metrics(reg,mods)
