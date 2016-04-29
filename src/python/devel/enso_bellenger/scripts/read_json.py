import json
import string

execfile('./plot_metrics.py')
execfile('./plot_metrics2.py')

test = True

way1 = True
way1 = False

if way1:
  mip = 'cmip5'
  exp = 'piControl'
  run = 'r1i1p1'
  fq = 'mo'
  realm = 'atm'
  var = 'ts'
  #var = 'pr'

  json_filename = 'ENSO_' + mip + '_' + exp + '_' + run + '_' + fq + '_' +realm + '_' + var

else:
  json_file = 'ENSO_cmip5_piControl_r1i1p1_mo_atm_ts.json'
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
    #if test == True:
    #  print(d)

stdv={}
mods=[]

if test:
  regs = ['Nino3'] # Test just one region
else:
  regs = ['Nino34', 'Nino3', 'Nino4', 'Nino12','TSA','TNA','IO']

mods = d.keys()
mods.sort()

reg_time = []
for mod in mods:
  reg_time.append(d[mod]['reg_time'])

for reg in regs:

  tmp = []
  for mod in mods:
    tmp.append(d[mod][reg]['std']['entire'])
  stdv[reg] = tmp[:]
  plot_metrics(reg,mods)

  del tmp[:]
  for mod in mods:
    tmp.append(float(d[mod][reg]['std_NDJ']['entire'])/float(d[mod][reg]['std_MAM']['entire']))
  stdv[reg] = tmp[:]
  plot_metrics2(reg,mods)
