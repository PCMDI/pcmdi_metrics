import glob
import datetime

realm = 'atm'
MIP = 'cmip6'    #'CMIP6'
exp = 'historical'  # historical or amip
#exp = 'amip'
start = '1981-01'
end = '2005-12'
if MIP=='cmip5':rn = 'r1i1p1'
if MIP=='cmip6':rn = 'r1i1p1f1'  # TO GET ONE RUN FROM EACH MOD NEED r1i1p1f1 AND r1i1p1f2

ver = datetime.datetime.now().strftime('v%Y%m%d')

ver_of_latest = 'v20201118'  #'v20200526'   #'v20200511'  #'v20200420'  #'v20200420'   #'v20200124'  #'v20191101'

modpath = '/work/cmip-dyn/' + MIP + '/CMIP/' + exp + '/atmos/mon/' 
modpath = '/p/user_pub/xclim/' + MIP + '/CMIP/' + exp + '/atmos/mon/'
modpath = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' + ver_of_latest + '/' + MIP + '/' + exp + '/atmos/mon/'
modpath = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' +  MIP + '/' + exp + '/atmos/mon/'

modpath = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' +  ver_of_latest + '/' + MIP + '/' + exp + '/atmos/mon/'

model = []
lst = glob.glob(modpath + 'rlut/*.r1*.xml')
print(len(lst))
for l in lst:
  mod = l.split('.')[4]  #[6]
  print(l.split('.')) 
  if mod not in model:model.append(mod)

#model = ['CESM2','ACCESS-CM2']  #,'TaiESM1']
#model = ['ACCESS-CM2']  #,'TaiESM1']


print(model)
modpath = modpath + '%(variable)/'


####

#variable = ['ts','pr','tas','prw','psl','tauu','tauv','uas','vas','huss','hurs','sfcWind']
#variable = ['rlut','rsut','rsutcs','rlutcs','rsdt','rsus','rsds','rlds','rlus','rldscs','rsdscs']
variable = ['ta','ua','va','zg','hur','hus']


#variable = ['sfcWind']

#variable = ['rsut','rsdt']  # TESTING
#variable = ['pr']   # TESTING

# CMIP6 TESTING ###################################################
#model= ['GFDL-CM2p1','CNRM-CM5']  # TESTING
#model = ['GFDL-CM4']
#model = ['IPSL-CM6A-LR']
bad_mods = []  #['GFDL-CM4']
#bad_mods = ['GFDL-CM4'] #,'IPSL-CM6A-LR']
for m in model:
  if m in bad_mods: model.remove(m)
#model = ['GISS-E2-1-G','CNRM-CM6','MIROC6']
### END CMIP6 #####################################################

#model = ['GFDL-CM4']

print('mods are ', model)

filename_template = MIP + '.'+'CMIP.'+ exp + '.*.' +  '%(model).' + rn + '.mon.' + '%(variable)' + '.atmos.glb*.xml'
filename_template = MIP + '.'+ exp +  '.%(model).' + rn + '.mon.' + '%(variable)' + '.xml'

#output_filename_template = MIP + '.'+ exp + '.' + '%(model).'+ rn + '.mon.' + '%(variable).' +  start.replace('-','') + '-' + end.replace('-','') + '.AC.' + ver + '.nc'
output_filename_template = MIP + '.'+ exp + '.' + '%(model).'+ rn + '.mon.' + '%(variable).' +  start.replace('-','') + '-' + end.replace('-','') + '.AC.' + ver + '.nc'

#results_dir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/' + MIP + '/' + exp + '/' + ver + '/%(variable)' 

#results_dir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/data/CMIP_CLIMS/' + MIP + '/' + exp + '/' + ver + '/%(variable)'
results_dir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/' + MIP + '/' + exp + '/' + ver + '/%(variable)'

num_workers = 15 
#granularize = ["variable"]
granularize = ["model", "variable"]
