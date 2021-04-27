import json

pmp_vars = {}

pmp_vars['variability_mode'] = {} 
pmp_vars['variability_mode']['mon'] = {}
pmp_vars['variability_mode']['mon'] = ['ts','psl'] 
pmp_vars['variability_mode']['fx'] = ['sftlf']

pmp_vars['monsoon_wang'] = {}
pmp_vars['monsoon_wang']['mon'] = {}
pmp_vars['monsoon_wang']['mon'] = ['pr']
pmp_vars['monsoon_wang']['fx'] = ['sftlf']

pmp_vars['monsoon_sperber'] = {}
pmp_vars['monsoon_sperber']['day'] = {}
pmp_vars['monsoon_sperber']['day'] = ['pr']
pmp_vars['monsoon_wang']['fx'] = ['sftlf']

pmp_vars['mjo'] = {}
pmp_vars['mjo']['day'] = {}
pmp_vars['mjo']['day'] = ['pr']
pmp_vars['mjo']['fx'] = ['sftlf']

pmp_vars['diurnal'] = {}
pmp_vars['diurnal']['3hr'] = {}
pmp_vars['diurnal']['3hr'] = ['pr']
pmp_vars['diurnal']['fx'] = ['sftlf']

pmp_vars['enso'] = {}
pmp_vars['enso']['mon'] = ['pr','psl','tas','tauu','tauv'],
pmp_vars['enso']['fx'] = ['sftlf']

pmp_vars['mean_climate'] = {}
pmp_vars['mean_climate']['mon'] = ['ta','ua','va','zg','hur','hus','pr','prw','psl','sfcWind','tas','huss','hurs','tauu','tauv','rlut','rsdt','rsut','rsutcs','rlutcs','rltcre','rstcre','rsds','rlds','rlus','rsus'],
pmp_vars['mean_climate']['fx'] = ['sftlf']


out_file = open("pmp_vars_needed.json", "w")
json.dump(pmp_vars, out_file, indent=4, separators=(',', ': '))




