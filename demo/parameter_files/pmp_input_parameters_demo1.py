################################################################################
#  THIS IS A DEMO INPUT PARAMETER FILE FOR THE PCMDI METRICS PACKAGE (PMP V1.1)
#  THIS IS A VERY SIMPLE EXAMPLE, ONLY COMPUTING STATISTICS FOR ONE MODEL VERSION AND ONE VARIABLE 
#  SAMPLE MODEL AND OBSERVATIONAL DATA TO RUN THIS CODE ARE AVAILABLE FROM: 
#  http://oceanonly.llnl.gov/gleckler1/pmp-demo-data/pmpv1.1_demodata.tar
#  Download this demo data and untar in the directory you plan to run the tests.  
#  For more info, see https://github.com/PCMDI/pcmdi_metrics/wiki/Using-the-package

# NOTES FOR PYTHON NEWBIES: ON ANY GIVEN LINE, ANTHING TO THE RIGHT OF A "#" IS CONSIDERED A COMMENT IN PYTHON  
# IN THIS SIMPLE EXAMPLE WE DEFINE CHARACTER STRINGS, BUT ALSO ONE OF THE MOST BASIC AND POWERFUL PYTHON OBJECTS KNOWN AS A LIST.  
# PYTHON LISTS ARE DEFINED WITH SQUARE BRACKETS [] ... FOR MORE INFO SEE: https://docs.python.org/2/tutorial/datastructures.html
################################################################################

## FIRST USE OF A PYTHON LIST, IN THIS CASE IT HAS ONLY ONE ENTRY 
model_versions = ['ACCESS1-0']   # THIS IS A MANDETORY ENTRY FOR DOCUMENTING RESULTS

###############################################################################
## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
## ROOT PATH FOR MODELS CLIMATOLOGIES
## THE MODEL AND OBSERVATIONAL DATA USED FOR THIS TEST CAN BE DOWNLOADED FROM: :wq

#mod_data_path = '/work/metricspackage/mod_clims/cmip5-amip'
mod_data_path = './cmip5clims_metrics_package-amip/'
filename_template = "pr_ACCESS1-0_Amon_amip_r1i1p1_198001-200512-clim.nc"
## ROOT PATH FOR OBSERVATIONS
obs_data_path = './obs/'

## DIRECTORY WHERE TO SAVE RESULTS
case_id = 'simple-test1'
metrics_output_path = './pmp-test/%(case_id)/'  # USER CHOOSES, RESULTS STORED IN  metrics_output_path + case_id   
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

save_mod_clims = False 






