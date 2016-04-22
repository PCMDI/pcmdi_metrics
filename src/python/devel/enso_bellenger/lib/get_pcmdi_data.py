def get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,var,run):
#  execfile('/export/durack1/git/pylib/durolib.py')
#  from durolib import trimModelList
   if realm == 'atm': Realm = 'Amon'
   if mip == 'cmip5': pin = '/work/' + mip + '/' + exp + '/' + realm + '/' + fq + '/' + var + '/' + mip + '.' + mod + '.' + exp + '.' + run + '.' + fq + '.' + realm + '.' + Realm + '.' + var + '*.xml' 
#  print pin
## PAUL DURACK's VERSION TRAPPING
   lst0 = os.popen('ls ' + pin).readlines()
   modelFileListTrimmed = trimModelList(lst0)
   latest = modelFileListTrimmed[0][:-1]
   return(latest)

def get_all_mip_mods(mip,exp,fq,realm,var):
   if realm == 'atm': Realm = 'Amon'
   if mip == 'cmip5': pin = '/work/' + mip + '/' + exp + '/' + realm + '/' + fq + '/' + var + '/' + mip + '.*.' + exp + '.' + run + '.' + fq + '.' + realm + '.' + Realm + '.' + var + '*.xml'
#  if mip == 'cmip5': pin = '/work/' + mip + '/' + exp + '/' + realm + '/' + fq + '/' + var + '/' + mip + '.*IPSL*.' + exp + '.' + run + '.' + fq + '.' + realm + '.' + Realm + '.' + var + '*.xml'
   lst = os.popen('ls ' + pin).readlines()
   mods = []
   for l in lst:
     mod = string.split(l,'.')[1]
     if mod not in mods: mods.append(mod)
   return(mods)

