def get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,var,run):
   #from durolib import trimModelList
   if realm == 'atm': Realm = 'Amon'
   if mip == 'cmip5': pin = '/work/' + mip + '/' + exp + '/' + realm + '/' + fq + '/' + var + '/' + mip + '.' + mod + '.' + exp + '.' + run + '.' + fq + '.' + realm + '.' + Realm + '.' + var + '*.xml' 
   lst0 = os.popen('ls ' + pin).readlines()
   modelFileListTrimmed = trimModelList(lst0)
   latest = modelFileListTrimmed[0][:-1]
   return(latest)

def get_latest_pcmdi_mip_data_path_as_list(mip,exp,mod,fq,realm,var,run):
   #from durolib import trimModelList
   if realm == 'atm': Realm = 'Amon'
   if mip == 'cmip5': pin = '/work/' + mip + '/' + exp + '/' + realm + '/' + fq + '/' + var + '/' + mip + '.' + mod + '.' + exp + '.' + run + '.' + fq + '.' + realm + '.' + Realm + '.' + var + '*.xml'

   #### TEMPORARY ####
   #if mod == 'GFDL-CM2p1' and mode == 'PDO':
   #  pin = '/work/lee1043/ESGF/CMIP5/GFDL-CM2p1/'+ mip + '.' + mod + '.' + exp + '.' + run + '.' + fq + '.' + realm + '.' + Realm + '.' + var + '*.xml'

   lst0 = os.popen('ls ' + pin).readlines()
   modelFileListTrimmed = trimModelList(lst0)
   latest = map(str.rstrip, modelFileListTrimmed)
   return(latest)

def get_latest_pcmdi_mip_lf_data_path(mip,mod,var):
   #from durolib import trimModelList
   if mip == 'cmip5': pin = '/work/' + mip + '/fx/fx/' + var + '/' + mip + '.' + mod + '.*.xml'
   lst0 = os.popen('ls ' + pin).readlines()
   modelFileListTrimmed = trimModelList(lst0)
   latest = modelFileListTrimmed[0][:-1]
   return(latest)

def get_all_mip_mods(mip,exp,fq,realm,var):
   if realm == 'atm': Realm = 'Amon'
   if mip == 'cmip5': pin = '/work/' + mip + '/' + exp + '/' + realm + '/' + fq + '/' + var + '/' + mip + '.*.' + exp + '.*.' + fq + '.' + realm + '.' + Realm + '.' + var + '*.xml'
   lst = os.popen('ls ' + pin).readlines()
   mods = []
   for l in lst:
     mod = string.split(l,'.')[1]
     if mod not in mods: mods.append(mod)
   return(mods)

def get_all_mip_mods_lf(mip,var):
   if mip == 'cmip5': pin = '/work/' + mip + '/fx/fx/' + var + '/' + mip + '.*.xml'
   lst = os.popen('ls ' + pin).readlines()
   mods = []
   for l in lst:
     mod = string.split(l,'.')[1]
     if mod not in mods: mods.append(mod)
   return(mods)
