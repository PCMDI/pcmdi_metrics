import json

# FOR CLIMS ONLY AT PRESENT. obs_defaults.py NEEDS TO BE UPDATED WITH OBSMIPs CHANGES
#PJG 20230802

exec(open('obs_defaults.py').read())
catalogue_path =  '../../catalogue/'
obs4MIPs_json = 'obs4MIPs_PCMDI_clims_byVar_catalogue_v20230519.json' 

dic = json.load(open(catalogue_path + obs4MIPs_json))

for v in dic.keys():
 for pri in ['default','alternate1','alternate2','alternate3']:
  try:
   dic[v][pri] = obs_dic_in[v][pri]
  except:
   print(v,' ','MISSING ',pri)

pmpjson = obs4MIPs_json.replace('PCMDI','PMP-defaults')

with open(pmpjson, "w") as outdic:
    json.dump(dic, outdic, indent=4, sort_keys=True)



