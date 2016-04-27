import json

execfile('./plot_metrics.py')
execfile('./plot_metrics2.py')

var = 'ts'
#var = 'pr'

test = True

with open('test_ENSO_cmip5_piControl_'+var+'.json') as json_data:
    d = json.load(json_data)
    #if test == True:
    #  print(d)

stdv={}
mods=[]

if test:
  regs = ['Nino3'] # Test just one region
else:
  regs = ['Nino34', 'Nino3', 'Nino4', 'Nino12','TSA','TNA','IO']

for reg in regs:
  mods = d.keys()
  mods.sort()
  tmp = []
  for mod in mods:
    tmp.append(d[mod][reg]['std'])
  stdv[reg] = tmp[:]
  plot_metrics(reg,mods)

  del tmp[:]
  for mod in mods:
    tmp.append(float(d[mod][reg]['std_NDJ'])/float(d[mod][reg]['std_MAM']))
  stdv[reg] = tmp[:]
  plot_metrics2(reg,mods)
