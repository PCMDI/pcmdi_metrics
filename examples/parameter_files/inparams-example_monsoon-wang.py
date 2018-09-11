# SAMPLE PARAMETER FILE TO RUN PMP's MONSOON_WANG METRICS

# TO RUN THIS AND OTHER EXAMPLES, download and untar the following data: https://pcmdi.llnl.gov/pss/pmpdata/pmp_inparam_exampledata_07192018.tar 

# EXECUTION WITH THE PMP
# >  mpindex_compute.py -p inparams-example_monsoon-wang.py 

# ALTERNATE EXECUTION VIA THE COMMAND LINE
# > .... 

### NEEDED IMPROVEMENTS
# Add regridding options here and in Monsoon driver

import datetime
import glob
import sys
import genutil
import json

########################

# EXPERIMENT and case_id (free form, used for basic provenance when exercising PMP)

# Run case, MIP, exp
case_id = 'test1'
MIP = 'cmip5'
experiment = 'historical'

########################
# INPUT PATHS

# Create a StringConstructor object (see https://cdat.llnl.gov/Jupyter/EasilyCreatingStringsWithTemplating/EasilyCreatingStringsWithTemplating.html) 
root_dir = './pmp_inparam_exampledata_07192018/' # or some other location where the example data has been untarred 
file_template = root_dir + "modeldata/pr_%(model)_Amon_%(experiment)_r1i1p1_198101-200512-clim.nc"
modpath = genutil.StringConstructor(file_template)
#print 'modpath is ', type(modpath),' ', type(modpath()),' ', modpath()

reference_data_path = root_dir + "obs/pr_GPCP_000001-000012_ac.nc"

########################

# GET LIST OF ALL POSSIBLE MODELS

f  = open(sys.prefix + "/share/pmp/cmip_model_list.json")
possible_mod_dic = json.load(f)
#modnames = possible_mod_dic[MIP][experiment] 
#print 'modnames are ', modnames

# OR SELECT A SUBSET OF MODELS
modnames = ['ACCESS1-3']

########################
# OUTPUT PATHS (METRICS AND DIAGNOSTICS)

results_base_dir = './pmp-test/' 
outpathjsons = results_base_dir + 'metrics_results/monsoon/monsoon_wang/cmip5/' + experiment + '/' + case_id
outpathdiags = outpathjsons.replace('metrics','diagnostic') 

########################
# INTERPOLATION OPTIONS

# ESMF options NOT YET IMPLEMENTED 
#regrid_method = 'linear'  #'conservative'
#regrid_method = 'conservative'
#regrid_tool = 'ESMF'
regrid_method = 'regrid2'
regrid_tool = 'regrid2'

#######################
# FILENAME (JSON) FOR METRICS

d_date = datetime.datetime.now()
reg_format_date = d_date.strftime("%Y-%m-%d-%I-%M-%S")

jsonname = 'monsoon-wang_CMIP5_historical' + '-' + regrid_tool + '_' + regrid_method + '_' + reg_format_date

