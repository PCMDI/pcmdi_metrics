import  genutil
from input_parameters import *
import sys, os, string
import cdms2 as cdms

################################################################################
## OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
### BEGIN USER INPUT  
### END USER INPUT
################################################################################

### DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
### BEGIN USER INPUT 
test_case = 'cmip5_test'   # USER INPUT: DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
mod_data_path = '/work/gleckler1/processed_data/metrics_package/inhouse_model_clims/' # USER INPUT: ROOT PATH FOR OUTPUT DIR OF METRICS RESULTS
#mod_data_path = '/work/gleckler1/processed_data/cmip5clims-AR5-frozen_1dir/' 
interpolated_model_output_path = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims/'+ test_case + '/' 
### END USER INPUT

### MODEL VERSIONS TO BE TESTED
### BEGIN USER INPUT
model_versions = ['samplerun1','samplerun2']   # USER INPUT: DIFFERENT MODEL VERSIONS CAN BE INCLUDED HERE
model_versions = ['GFDL-ESM2G']  #  USER INPUT: LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME

test_case = 'sampletest'   # USER INPUT: DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED

### ALL CMIP5
#model_versions = []
#lst = os.popen('ls ' + mod_data_path + test_case + '/' + '*rlut*').readlines()
#for l in lst:
#  mod = string.split(l,'.')[1]
#  if mod not in model_versions: model_versions.append(mod)

#model_versions = ['FGOALS-g2']
#print model_versions
#w = sys.stdin.readline()

#model_versions = [model_versions[0]]

### END USER INPUT

### SAVE INTERPOLATED MODEL CLIMATOLGIES ?
save_mod_clims = 'y'   # 'y'  or 'n'


########################################################################################################
### DATA STRUCTURE OF NEW MODEL CLIMATOLOGIES
### CHOOSE AN OPTION: 
### data_structure = 'simple': SEPERATE FILE FOR EACH VARIABLE
### data_structure = 'cmip5':  FILENAME TEMPLATE INCLUDES MODEL VERSION, RUN#, ETC."
### BEGIN USER INPUT
data_structure = 'simple' # USER INPUT: SEE ABOVE CHOICES
### BEGIN USER INPUT

def model_output_structure(model_version, variable):
 dir_template = "%(root_modeling_group_clim_directory)/%(test_case)/" 
 file_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable).ver-1.%(period).AC.%(ext)" 

 ### CONSTRUCT PATH
 D=genutil.StringConstructor(dir_template)
 D.root_modeling_group_clim_directory = mod_data_path
 D.test_case = test_case
 data_location = D()

 ### CONSTRUCT FILENAME 
 F = genutil.StringConstructor(file_template) 
 F.model_version = model_version
 F.table_realm = 'atm.Amon'
 if variable in ['tos','sos','zos']:  F.table_realm = 'ocn.Omon'
 F.variable = variable
 F.ext='nc'
 F.period = '1980-2005'
 filename = F()

 return data_location,filename

def output_interpolated_model_data(dm, var, targetGrid,regrid_method,model_output_location):

 model_output_location = string.replace(model_output_location,'.nc','.' + regrid_method + '.' + targetGrid + '.nc') 

 g = cdms.open(model_output_location,'w+')
 dm.id = var
 g.write(dm)
 g.close() 


#################################################################################
### END OPTIONS SET BY USER
#################################################################################
