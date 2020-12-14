import  genutil
import datetime
import json
import os,sys

ver = datetime.datetime.now().strftime('v%Y%m%d')

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
################################################################################
case_id = 'E3SM'
exp = 'historical'
user_notes = 'Provenance and results'
# If 'y', run only 'regional' variable set:
regional = 'n' # 'n'

######################
## VERSION INFORMATION
modver = 'v20200421'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
all_mods_dic = ['E3SM-1-0']
test_data_set = ''
test_data_set.sort()

print(len(test_data_set),' ',test_data_set)

print('----------------------------------------------------------------')

simulation_description_mapping = {'creation_date' : 'creation_date', 'tracking_id': 'tracking_id',}

### VARIABLES AND OBSERVATIONS TO USE
realm = 'Amon'
#realm = 'Omon'

##########################
## WITHOUT PARALLELIZATION
#original: vars = ['psl','tauu','tauv','tas','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500','pr','rltcre','rstcre','rt','rst','rlut']
#all obs: vars = ['hfls','hfns','hfss','hur','hus','pr','prw','psl','rlds','rldscs','rlscre','rltcre','rlus','rlut','rlutcs','rnscre','rsds','rsdscs','rsdt','rsscre','rstcre','rsus','rsuscs','rsut','rsutcs','rt','sfcWind','ta_850','tas','tauu','tauv','ts','ua_200','ua_850','uas','va_200','va_850','vas','zg_500']
vars = ['hfls','zg_500']

#if regional == 'y':
#  vars = ['tas','ts','psl','sfcWind']  #,'tauu','tauv']   ## THESE DO NOT WORK WITH PARALLELIZATON

#######################
## WITH PARALLELIZATION
#vars = [['psl',],['pr',],['prw',],['tas',],['uas',],['vas',],['sfcWind',],['tauu'],['tauv']]
#vars = [['ta_850',],['ta_200',],['ua_850',],['ua_200',],['va_850',],['va_200',],['zg_500']]
#vars = [['rlut',],['rsut',],['rsutcs',],['rlutcs',],['rsdt',],['rsus',],['rsds',],['rlds',],['rlus',],['rldscs',],['rsdscs']]

# ALL BUT NOT tas ts psl sfcwind tauu tauv
if regional == 'n':
  # Special formatting for regional vars with parallelization
  vars = [['pr',],['prw',],['uas',],['vas',],['ta_850',],['ta_200',],['ua_850',],['ua_200',],['va_850',],['va_200',],['zg_500'],['rlut',],['rsut',],['rsutcs',],['rlutcs',],['rsdt',],['rsus',],['rsds',],['rlds',],['rlus',],['rldscs',],['rsdscs'],['rltcre',],['rstcre',],['rt',]]

###########################
## MODEL SPECIFC PARAMETERS
model_tweaks = {
    ## Keys are model accronym or None which applies to all model entries
    None : {
      ## Variables name mapping
      'variable_mapping' : { 'rlwcrf1' : 'rlutcre1'},
      },
    }

## USER CUSTOMIZED REGIONS
import cdutil

if regional == 'y':

 regions_specs = {'Nino34': {'value':0.,'domain':cdutil.region.domain(latitude=(-5.,5.), longitude=(190.,240.))},
         'ocean' : {'value':0.,'domain':cdutil.region.domain(latitude=(-90.,90))},
         'land' : {'value':100.,'domain':cdutil.region.domain(latitude=(-90.,90))},
         'ocean_50S50N' : {'value':0.,'domain':cdutil.region.domain(latitude=(-50.,50))},
         'ocean_50S20S' : {'value':0.,'domain':cdutil.region.domain(latitude=(-50.,-20))},
        'ocean_20S20N': {'value':0.,'domain':cdutil.region.domain(latitude=(-20.,20))},
         'ocean_20N50N' : {'value':0.,'domain':cdutil.region.domain(latitude=(20.,50))},
         'ocean_50N90N' : {'value':0.,'domain':cdutil.region.domain(latitude=(50.,90))},
        '90S50S' : {'value':None,'domain':cdutil.region.domain(latitude=(-90.,-50))},
        '50S20S' : {'value':None,'domain':cdutil.region.domain(latitude=(-50.,-20))},
        '20S20N': {'value':None,'domain':cdutil.region.domain(latitude=(-20.,20))},
        '20N50N' : {'value':None,'domain':cdutil.region.domain(latitude=(20.,50))},
        '50N90N' : {'value':None,'domain':cdutil.region.domain(latitude=(50.,90))},
        'NH' : {'value':None,'domain':cdutil.region.domain(latitude=(0.,90))},
        'SH' : {'value':None,'domain':cdutil.region.domain(latitude=(-90.,0))},
        'NHEX_ocean' : {'value':0.,'domain':cdutil.region.domain(latitude=(0.,90))},
        'SHEX_ocean' : {'value':0.,'domain':cdutil.region.domain(latitude=(-90.,0))},
        'NHEX_land' : {'value':100.,'domain':cdutil.region.domain(latitude=(20.,90))},
        'SHEX_land' : {'value':100.,'domain':cdutil.region.domain(latitude=(-90.,-20.))}}
#       'GLOBAL' : {'value':0.,'domain':cdutil.region.domain(latitude=(-90.,90.))},

 regions = {'tas': [None, 'land','ocean', 'ocean_50S50N','NHEX_land','SHEX_land'],
          'tauu': [None, 'ocean_50S50N'],
          'tauv': [None,'ocean_50S50N'],
          'psl': [None,'ocean', 'ocean_50S50N','NHEX_ocean','SHEX_ocean'],
          'sfcWind': [None,'ocean', 'ocean_50S50N','NHEX_ocean','SHEX_ocean'],
          'ts': [None,'ocean', 'ocean_50S50N','NHEX_ocean','SHEX_ocean'],
           'tos': [None]}

## USER CAN CUSTOMIZE REGIONS VALUES NAMES
#regions_values = {'land':100.,'ocean':0.}

# Observations to use at the moment 'default' or 'alternate'
ref = 'all'
reference_data_set = ['default']  # ['default']  #,'alternate1']  #,'alternate','ref3']
ext = '.xml' # .xml or .nc

# INTERPOLATION OPTIONS
target_grid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
targetGrid = target_grid
target_grid_string = '2p5x2p5'
regrid_tool       = 'regrid2' #'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'regrid2'  #'conservative'  #'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: 'regrid2','esmf'
regrid_method_ocn = 'conservative'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS
period = '1981-2005'
realization = 'r1i1p1f1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_test_clims = True # True or False

################################################
## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
filename_template = 'cmip6.historical.%(model_version).r1i1p1f1.mon.%(variable).198101-200512.AC.' + modver + '.nc'

## Templates for MODEL land/sea mask (sftlf)
## filename template for landsea masks ('sftlf')
generate_sftlf = True    # ESTIMATE LAND SEA MASK IF NOT FOUND
sftlf_filename_template = 'cmip6.historical.%(model_version).sftlf.nc'   #'sftlf_%(model_version).nc'

## ROOT PATH FOR MODELS CLIMATOLOGIES
test_data_path = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip6/historical/' + modver + '/%(variable)/'

## ROOT PATH FOR OBSERVATIONS
reference_data_path = '/p/user_pub/PCMDIobs/PCMDIobs2_clims/'
custom_observations = './pcmdiobs2_clims_byVar_catalogue_v20200615.json'

print('CUSTOM OBS ARE ', custom_observations)
if not os.path.exists(custom_observations):
  sys.exit()

########################################################
### DIRECTORY AND FILENAME FOR OUTPUTING METRICS RESULTS
results_dir = '/export/ordonez4/pmp_results/'

 metrics_output_path = results_dir + '/pmp_results/pmp_v1.1.2/metrics_results/mean_climate/cmip6/historical/%(case_id)/' # All SAME FILE
 output_json_template = '%(variable)%(level).cmip6.historicalz.%(regrid_method).' + target_grid_string + '.'  + case_id # ALL SAME FILE

############################################################
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
test_clims_interpolated_output = results_dir + '/pmp_results/pmp_v1.1.2/diagnostic_results' + '/interpolated_model_clims/cmip6/historical/' + case_id

## FILENAME FOR INTERPOLATED CLIMATOLGIES OUTPUT
filename_output_template = 'cmip6.%(model_version).historical.r1i1p1.mo.%(variable)%(level).%(period).interpolated.%(regrid_method).%(region).AC.' + case_id + '%(ext)'

######################
## FOR PARALLELIZATION
if regional == 'n':
 num_workers = 20  #17
 granularize = ['vars']
