import  genutil, os.path, time
from datetime import datetime

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
#
################################################################################


## Keywords for the indexation of the metrics results
# -> Model : ModelActivity, ModellingGroup, Model, Experiment, Simname (realization), ModelFreeSpace, Login, Center, SimTrackingDate
# -> Ref : RefActivity, RefName, RefType, RefTrackingDate, RefFreeSpace
# -> Regridding : RegridMethod, Gridname, GridResolution
# -> Metric : Period, MetricName, DataType, Domain (land, ocean...), Region, GeographicalLimits, Variable, MetricFreeSpace, P_value, MetricContactExpert, MetricTrackingDate


# -------------------------------------------------------------------------------------------------------------------
## Which metrics?
## PCMDI_metrics, IPSL_metrics, NEMO_metrics...
import pcmdi_metrics

funlist=[pcmdi_metrics.pcmdi.compute_MyCustomMetrics]
def my_custom(var,dm,do):
  out = {}
  for f in funlist:
      out.update(f(var,dm,do))
  return out

compute_custom_metrics = my_custom
# => if you want to compute your custom metrics, set compute_custom_metrics = my_custom ;
# => if you want to switch off the computation of the custom metrics, do not define compute_custom_metrics (comment it)

# Set compute_custom_only to True if you want to compute ONLY your custom metrics
# If you want to compute your custom metrics AND the PCMDI metrics, set compute_custom_only to False
compute_custom_only = True
#compute_custom_only = False


# -------------------------------------------------------------------------------------------------------------------
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions = ['GFDL-ESM2G',]

## Creation date of the metric
metricCreationDate = time.strftime('%Y-%m-%d %H:%M:%S')

simulation_description_mapping = {
            "metricCreationDate":"metricCreationDate",
           }


# -------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------------------
## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
case_id = 'Test_example_compute_custom_only'
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME

### VARIABLES AND OBSERVATIONS TO USE
### VARIABLES AND OBSERVATIONS TO USE
vars = ['ua_850']

## regions of mask to use when processing variables
regions = {}


# Observations to use at the moment "default", "alternate1", "alternate2", "alternate3", or "all" (last two are not always available)
ref = 'default'

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'esmf' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# Do you want to generate a land-sea mask? True or False
generate_sftlf = True

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = False # True or False

# -------------------------------------------------------------------------------------------------------------------



# -------------------------------------------------------------------------------------------------------------------
## Model tweaks : here you can define a correspondance table for the variables names
model_tweaks = { model_versions[0] :
                    { 'variable_mapping' :
                        {
                        }
                    }
               }

# -------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------------------
## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## Templates for climatology files
filename_template = 'cmip5_GFDL-CM3_historical_r4i1p1_mon_atmos_Amon_ua_latest_198001-200512_clim.nc'
period='198001-200512'
realization='r4i1p1'

## ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/data/igcmg/database/CMIP5_SE/historical/atmos/mon/ua/'

## ROOT PATH FOR OBSERVATIONS
#obs_data_path = 'my_obs_data_path/'
obs_data_path = '/data/jservon/Evaluation/ReferenceDatasets/PCMDI-MP/obs/'

## DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = 'my_metrics_output_path/'

## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = ''


# -------------------------------------------------------------------------------------------------------------------

