################################################################################
#  SAMPLE INPUT PARAMETER FILE FOR THE PCMDI METRICS PACKAGE (PMP V1.1)
#  THIS IS A VERY SIMPLE EXAMPLE, ONLY COMPUTING STATISTICS FOR ONE MODEL VERSION AND ONE VARIABLE 
#  SAMPLE MODEL AND OBSERVATIONAL DATA TO RUN THIS CODE ARE AVAILABLE FROM: 
# 
# NOTES FOR PYTHON NEWBIES: ON ANY GIVEN LINE, ANTHING TO THE RIGHT OF A "#" IS CONSIDERED A COMMENT IN PYTHON  
# IN THIS SIMPLE EXAMPLE WE DEFINE CHARACTER STRINGS, BUT ALSO ONE OF THE MOST BASIC AND POWERFUL PYTHON OBJECTS KNOWN AS A LIST.  
# PYTHON LISTS ARE DEFINED WITH SQUARE BRACKETS [] ... FOR MORE INFO SEE: https://docs.python.org/2/tutorial/datastructures.html
################################################################################

## FIRST USE OF A PYTHON LIST, IN THIS CASE IT HAS ONLY ONE ENTRY 
model_versions = ['ACCESS1-0']   # THIS IS A MANDETORY ENTRY FOR DOCUMENTING RESULTS

###############################################################################
## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
## ROOT PATH FOR MODELS CLIMATOLOGIES
#mod_data_path = '/work/metricspackage/mod_clims/cmip5-amip'
mod_data_path = './demo_obs_model_data/mods/'
filename_template = "pr_Amon_ACCESS1-0_amip_r1i1p1_197901-198912-clim-ac.nc"
## ROOT PATH FOR OBSERVATIONS
obs_data_path = './demo_obs_model_data/obs/'

## DIRECTORY WHERE TO SAVE RESULTS
case_id = 'simple-test1'
metrics_output_path = './pmp-test/'  # USER CHOOSES, RESULTS STORED IN  metrics_output_path + case_id   
###############################################################################

# OBSERVATIONS TO USE: CHOICES INCLUDE 'default','alternate1','alternate2',... AND ARE VARIABLE DEPENDENT 
ref = ['default']  #,'alternate1','alternate2']

## A PYTHON LIST OF VARIABLES TO COMPUTE STATISTICS
vars = ['pr']  # THIS EXAMPLE ONLY INCLUDES ONE FIELD, PRECIPICATION

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS (required in PMP v1.1)
period = '1979-1989'  # PERIOD OF CLIMATOLOGY
realization = 'r1i1p1' # REALIZATION








