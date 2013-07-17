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
### END USER INPUT

### MODEL VERSIONS TO BE TESTED
### BEGIN USER INPUT

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



########################################################################################################
### DATA STRUCTURE OF NEW MODEL CLIMATOLOGIES
### CHOOSE AN OPTION: 
### data_structure = 'simple': SEPERATE FILE FOR EACH VARIABLE
### data_structure = 'cmip5':  FILENAME TEMPLATE INCLUDES MODEL VERSION, RUN#, ETC."
### BEGIN USER INPUT
data_structure = 'simple' # USER INPUT: SEE ABOVE CHOICES
### BEGIN USER INPUT

#################################################################################
### END OPTIONS SET BY USER
#################################################################################
