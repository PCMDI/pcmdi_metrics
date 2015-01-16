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
which_metrics = 'PCMDI_metrics'


# -------------------------------------------------------------------------------------------------------------------
## Path/Filename
path_and_filename = 'targetfile'

## Amount of attributes provided with the results
# => Standard = correspond to the standard amount of information that allows using the portrait plot
# => IPSL_Extended = provides more information (more attributes) with the metrics to store the results in a database
attributes_provided = 'MyAttributes'

## From this, we get all the information we need
dum = str.split(path_and_filename,'/')

## File name
filename = dum[len(dum)-1]

## Model Path
mod_path = path_and_filename.rstrip(filename)

## Center
Center = "CCRT-TGCC"

## Login
Login = dum[5]

## Model versions
model_versions = [dum[7]]

## Simtype
experiment = dum[9]

## Realization => simname
realization = dum[10]

## ModelActivity
project_id = "IPSL-"+dum[8]

## Modelling Group
institute_id = "IPSL"

## Period
model_period = "_".join(str.split(filename,"_")[2:4])

## Model Free Space
ModelFreeSpace = "Tests libIGCM"

## ModelTrackingDate
creation_date = datetime.fromtimestamp(os.path.getmtime(path_and_filename)).strftime('%Y-%m-%d %H:%M:%S')
#SimTrackingDate = datetime.fromtimestamp(os.path.getmtime(path_and_filename)).strftime('%Y-%m-%d')

## Simulation description map
#if attributes_provided == 'standard':
#  simulation_description_mapping = {}
#else:
simulation_description_mapping = {
				    "model_period":"model_period",
				    "Login":"Login",
				    "Center":"Center",
				   }


# -------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------------------
## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
#case_id = 'IPSL_rewritten_file'
#case_id = 'Test_mapping'
case_id = institute_id+'-'+login+'-'+model_versions[0]+'-'+experiment+'-'+realization+'-'+model_period+'-'+attributes_provided
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME

### VARIABLES AND OBSERVATIONS TO USE
vars2D = ['pr','prw','tas','uas','vas','psl','rlut','rsut','rlutcs','rsutcs']
vars3D = ['ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500','hus_850']
strfilename = str.split(filename,'_')
if strfilename[len(strfilename)-1]=='histmth.nc':
   vars = vars2D
if strfilename[len(strfilename)-1]=='histmthNMC.nc':
   vars = vars3D

## regions of mask to use when processing variables
regions = {"tas" : ["land","ocean"],
           "uas" : [None,"land","ocean"],
           "vas" : [None,"land","ocean"],
           "pr" : [None,"land","ocean"],
           "psl": [None,"land","ocean"],
           "huss": [None,"land","ocean"],
           "prw": [None,"land","ocean"]
          }


#regions_values = {"terre":0.,}

# Observations to use at the moment "default", "alternate1", "alternate2", "alternate3", or "all" (last two are not always available)
ref = ['all']

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'esmf' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# Do you want to generate a land-sea mask? True or False
generate_sftlf = True

# Mask file
#MaskFilePath = '/data/jservon/Evaluation/grids/'
#MaskFileName = 'LMDZ4.0_9695_grid.nc'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = False # True or False

# -------------------------------------------------------------------------------------------------------------------



# -------------------------------------------------------------------------------------------------------------------
## Model tweaks : here you can define a correspondance table for the variables names

model_tweaks = { model_versions[0] :
                    { 'variable_mapping' :
                        {
                        'tas':'t2m',    # Surface Temperature
                        'pr':'precip',  # Precipitation
                        'prw':'prw',    # Precipitable Water
                        'psl':'slp',    # Sea Level Pressure
                        'hfss':'sens',  # Sensible heat flux
                        'hflx':'flat',  # Latent heat flux
                        'huss':'q2m',   # Near-surface specific humidity
                        'clt':'cldt',   # Total cloud cover
                        'tauu':'taux',  # Zonal wind stress
                        'tauv':'tauy',  # Meridional wind stress
                        'uas':'u10m',   # Near-surface zonal wind speed
                        'vas':'u10m',   # Near-surface meridional wind speed
                        'zg':'zg',       # 3D - Geopotential height (!!! Problem on this one)
                        'hus':'hus',      # 3D - Specific humidity
                        'ua':'ua',       # 3D - Zonal Wind
                        'va':'va',       # 3D - Meridional Wind
                        'ta':'ta',       # 3D - Temperature
                        'rlds':'LWdnSFC',      # Radiative - Downward longwave at surface
                        'rldscs':'LWdnSFCclr', # Radiative - Downward longwave at surface - Clear Sky
                        'rlus':'LWupSFC',      # Radiative - Upward longwave at surface
                        'rlut':'LWup200',      # Radiative - Upward longwave at TOA
                        'rlutcs':'LWup200clr', # Radiative - Upward longwave at TOA - Clear Sky
                        'rlwcrf':'',           # Radiative - Longwave Cloud radiative forcing
                        'rsds':'SWdnSFC',      # Radiative - Downward shortwave at surface
                        'rsdscs':'SWdnSFCclr', # Radiative - Downward shortwave at surface - Clear Sky
                        'rsdt':'SWdnTOA',      # Radiative - Downward shortwave at TOA
                        'rsus':'SWupSFC',      # Radiative - Upward shortwave at surface
                        'rsuscs':'SWupSFCclr', # Radiative - Upward shortwave at surface - Clear Sky
                        'rsut':'SWupTOA',      # Radiative - Upward shortwave at TOA
                        'rsutcs':'SWupTOAclr', # Radiative - Upward shortwave at TOA - Clea Sky
                        'rswcrf':''            # Radiative - Shortwave Cloud radiative forcing
                        }
                    }
               }

# -------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------------------
## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## Templates for climatology files
filename_template = filename

## ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = mod_path

## ROOT PATH FOR OBSERVATIONS
obs_data_path = 'my_obs_data_path/'

## DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = 'my_metrics_output_path/'

## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = ''
filename_output_template = "Metrics_%(model_version)."+experiment+"."+realization+".mo.%(table).%(variable).ver-1.%(period).%(region).AC.nc"

# -------------------------------------------------------------------------------------------------------------------

