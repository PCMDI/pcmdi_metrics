# Sea ice metrics parameter file

# List of models to include in analysis
test_data_set = [
    "E3SM-1-0"
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
