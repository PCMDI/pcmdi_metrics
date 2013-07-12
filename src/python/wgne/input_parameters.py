import  genutil

################################################################################
## OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
### BEGIN USER INPUT  
### END USER INPUT
################################################################################

### DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
### BEGIN USER INPUT 
obs_data_path = '/work/gleckler1/processed_data/metrics_package/'  # USER INPUT: ROOT PATH FOR OBSERVATIONS  
metrics_output_path = '/work/gleckler1/processed_data/metrics_package/metrics_results/'  # USER INPUT: ROOT PATH FOR METRICS RESULTS 
model_clims_interpolated_output = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims/'
### END USER INPUT

### VARIABLES AND OBSERVATIONS
vars = ['zos','pr','rlut','tas']
vars = ['tas','pr']
vars = ['pr','tas','tos']
vars = ['tos']
ref = 'default'  #  option is 'alternate' obs dataset

### INTERPOLATION
targetGrid = '2.5x2.5'   # OPTIONS: '2.5x2.5'
regrid_method = 'regrid2'   # OPTIONS: 'linear','regrid2'
regrid_method_ocn = 'linear'   # OPTIONS: 'linear', 'regrid2'

#################################################################################
### END OPTIONS SET BY USER
#################################################################################
