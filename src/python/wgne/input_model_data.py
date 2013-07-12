import  genutil
from input_parameters import *

################################################################################
## OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
### BEGIN USER INPUT ###  
### END USER INPUT ###
################################################################################

### BEGIN USER INPUT ###

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
mod_data_path = '/work/gleckler1/processed_data/metrics_package/inhouse_model_clims/'  # USER INPUT: ROOT PATH FOR OUTPUT DIR OF METRICS RESULTS

# MODEL VERSIONS TO BE TESTED
model_versions = ['samplerun1','samplerun2']   # USER INPUT: DIFFERENT MODEL VERSIONS CAN BE INCLUDED HERE
model_versions = ['GFDL-ESM2G']  #  USER INPUT: LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
test_case = 'sampletest'   # USER INPUT: DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED 

### SAVE INTERPOLATED MODEL CLIMATOLGIES ?
save_mod_clims = 'y'   # 'y'  or 'n'


### END USER INPUT

########################################################################################################
### DATA STRUCTURE OF NEW MODEL CLIMATOLOGIES
### CHOOSE AN OPTION: 
### data_structure = 'simple': SEPERATE FILE FOR EACH VARIABLE
### data_structure = 'cmip5':  FILENAME TEMPLATE INCLUDES MODEL VERSION, RUN#, ETC."
### BEGIN USER INPUT
data_structure = 'simple' # USER INPUT: SEE ABOVE CHOICES
### BEGIN USER INPUT

# EXAMPLE 1: ALL CLIMATOLOGY VARIABLES FOR A GIVEN EXPERIMENT ARE IN SEPERATE FILE
if data_structure == 'simple':
 dir_template = "%(root_modeling_group_clim_directory)/%(test_case)/" 
 file_template = "cmip5.%(model_version).historical.r1i1p1.mo.atm.Amon.%(variable).ver-1.1980-1999.AC.%(ext)" 
 template = dir_template + file_template  

 T=genutil.StringConstructor(template)
 T.root_modeling_group_clim_directory = mod_data_path
 T.table = 'Amon'
 T.test_case = test_case
 T.ext='nc'

 F = genutil.StringConstructor(file_template) 
 F.ext='nc'

# EXAMPLE 2: CLIMATOLOGY FILENAMES FOLLOW DRS CONVENTION USED IN CMIP5 
# EXAMPLE FILENAME STRUCTURE: cmip5.GFDL-ESM2G.historical.r1i1p1.mo.atm.Amon.tas.ver-1.1980-1999.AC.nc
if data_structure == 'simple':
 template = "%(root_modeling_group_clim_directory)/%(test_case)/cmip5.%(model_version).historical.r1i1p1.mo.atm.Amon.%(variable).ver-1.1980-1999.AC.%(ext)"
 T=genutil.StringConstructor(template)
 T.root_modeling_group_clim_directory = mod_data_path 
 T.table = 'Amon'
 T.test_case = test_case
 T.ext='nc'

if save_mod_clims == 'y':
 Tdir=genutil.StringConstructor(dir_template)
 Tdir.root_modeling_group_clim_directory = model_clims_interpolated_output 
 Tdir.test_case = test_case

#################################################################################
### END OPTIONS SET BY USER
#################################################################################
