################################################################################
#  THIS IS A SIMPLE EXAMPLE mean climate "parameter file" USED IN A DEMO EXECUTION OF THE PMP

#  For more info, see https://github.com/PCMDI/pcmdi_metrics/wiki/Using-the-package
#
# THIS PARAMETER FILE IS USED TO COMPUTE STATISTICS FOR ONE MODEL VERSION AND ONE VARIABLE ONLY

# NOTES FOR PYTHON NEWBIES: ON ANY GIVEN LINE, ANTHING TO THE RIGHT OF A "#" IS CONSIDERED A COMMENT IN PYTHON  
# IN THIS SIMPLE EXAMPLE WE DEFINE CHARACTER STRINGS, BUT ALSO ONE OF THE MOST BASIC AND POWERFUL PYTHON OBJECTS KNOWN AS A LIST.  
# PYTHON LISTS ARE DEFINED WITH SQUARE BRACKETS [] ... FOR MORE INFO SEE: https://docs.python.org/2/tutorial/datastructures.html
################################################################################
#
# First, we define the 'template' used by the PMP to construct file names and paths that correspond to the location of the model and observatinal data.
# Keywords in between %() will be automatically filled by PMP
# In this example we only use four of the 'official' keys: 'variable', 'model_version', 'realization' and 'period'
# some of these are defined later in the parameter file
# For a complete list of official keys see: 
filename_template = "%(variable)_%(model_version)_Amon_amip_%(realization)_%(period)-clim.nc"
# First lets define an case id to help us differentiate between many se of parameter files
# The python 'case_id' variable is optional in the parameter file
# non the less it is still a 'reserved' variable for the PMP
case_id = 'simple-test1'
# Now we will defined the list of models to use
# For this we use the 'reserved' python variable: model_versions
# THIS IS A MANDATORY ENTRY
# This is our first list of a python list, in this case there is only one entry
model_versions = ['ACCESS1-0']   

# The following lines will tell PMP where the data reside on your system
# Note that we could use the 'templating' filename system here as well
# Also note that these path are 'relative' to our current working path
# But one could use absolute paths as well
## MODELS DATA LOCATION
mod_data_path = 'pmp_demo/cmip5clims_metrics_package-amip/'
## ROOT PATH FOR OBSERVATIONS
obs_data_path = 'pmp_demo/obs/'

## DIRECTORY WHERE TO SAVE RESULTS
# USER CHOOSES, RESULTS STORED IN  metrics_output_path + case_id   
metrics_output_path = './pmp_demo/%(case_id)/'  

# OBSERVATIONS TO USE: CHOICES INCLUDE 'default','alternate1','alternate2',... AND ARE VARIABLE DEPENDENT 
ref = ['default']  #,'alternate1','alternate2']

## A PYTHON LIST OF VARIABLES TO COMPUTE STATISTICS
# THIS EXAMPLE ONLY INCLUDES ONE FIELD, PRECIPICATION
vars = ['pr']  

# INTERPOLATION (REGRIDDING) OPTIONS
# First our target grid, i.e the final grid onto which both model and obs will be put
# OPTIONS: '2.5x2.5' or an actual cdms2 grid object
targetGrid        = '2.5x2.5' 
# Now let's select which cdms2 regrid tool we will use
regrid_tool       = 'esmf' 
# Some regrid tools also require to specify which method of regriding to use
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method     = 'linear'

# SIMULATION PARAMETERS (required in PMP v1.1)
# These are manadatory in any PMP parameter file
# Beside remember that these are actually using in our templating system defined above
# PERIOD OF CLIMATOLOGY
period = '198001-200512'
# MODEL REALIZATION
realization = 'r1i1p1'
