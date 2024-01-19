# Sea ice metrics parameter file

# List of models to include in analysis
test_data_set = [
    "E3SM-1-0",
]

# realization can be a single realization, a list of realizations, or "*" for all realizations
realization = "r1i2p2f1"

# test_data_path is a template for the model data parent directory
test_data_path = "/p/user_pub/pmp/demo/sea-ice/links_siconc/%(model)/historical/%(realization)/siconc/"

# filename_template is a template for the model data file name
# combine it with test_data_path to get complete data path
filename_template = "siconc_SImon_%(model)_historical_%(realization)_*_*.nc"

# The name of the sea ice variable in the model data
var = "siconc"

# Start and end years for model data
msyear = 1981
meyear = 2010

# Factor for adjusting model data to decimal rather than percent units
ModUnitsAdjust = (True, "multiply", 1e-2)

# Template for the grid area file
area_template = "/p/user_pub/pmp/demo/sea-ice/links_area/%(model)/*.nc"

# Area variable name; likely 'areacello' or 'areacella' for CMIP6
area_var = "areacello"

# Factor to convert area units to km-2
AreaUnitsAdjust = (True, "multiply", 1e-6)

# Directory for writing outputs
case_id = "ex1"
metrics_output_path = "sea_ice_demo/%(case_id)/"

# Settings for the observational data
reference_data_path_nh = "/work/ordonez4/ice_conc_nh_ease2-250_cdr-v3p0_198801-202012.nc"
reference_data_path_sh = "/work/ordonez4/ice_conc_sh_ease2-250_cdr-v3p0_198801-202012.nc"
ObsUnitsAdjust=(True,"multiply",1e-2)
reference_data_set="OSI-SAF"
osyear=1988
oeyear=2020
obs_var="ice_conc"
ObsAreaUnitsAdjust = (False, 0, 0)
obs_area_template = None
obs_area_var = None
obs_cell_area = 625 #km 2