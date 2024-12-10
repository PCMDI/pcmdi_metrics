# Settings for extremes driver
# flake8: noqa
# These settings are required
vars = ["tasmax"]  # Choices are 'pr','tasmax', 'tasmin', "tas"
test_data_set = ["BCSD"]
realization = ["r1i1p1f1"]
test_data_path = "/pscratch/sd/j/jsgoodni/testData/"
filename_template = "%(variable)_bcsd*.nc"

metrics_output_path = "/pscratch/sd/j/jsgoodni/pmp_results/drcdm/test/"

# Note: You can use the following placeholders in file templates:
# %(variable) to substitute variable name from "vars" (except in sftlf filenames)
# %(model) to substitute model name from "test_data_set"
# %(realization) to substitute realization from "realization"

# Optional settings
# See the README for more information about these settings
case_id = "test_tasmax"
# 1976 - 2005
reference_data_path = "/pscratch/sd/j/jsgoodni/testData/tasmax_obs1.nc"
reference_data_set = ["GMFD"]
reference_filename_template = "%(variable)_obs.nc"

shp_path = "/pscratch/sd/j/jsgoodni/shapefiles/cb_2018_us_state_20m.shp"
attribute = "NAME"
region_name = "California"


# sftlf_filename_template = '/p/css03/esgf_publish/CMIP6/CMIP/MIROC/MIROC6/piControl/r1i1p1f1/fx/sftlf/gn/v20190311/sftlf_fx_MIROC6_piControl_r1i1p1f1_gn.nc'

ModUnitsAdjust_precip = (
    True,
    "multiply",
    86400.0,
    "mm/day",
)  # Convert model units from kg/m2/s to mm/day

ModUnitsAdjust_temperature = (True, "KtoF", 0, "F")


#
if vars[0] == "pr":
    ModUnitsAdjust = ModUnitsAdjust_precip  # precip variable
else:
    ModUnitsAdjust = ModUnitsAdjust_temperature  # temperature variable
    ObsUnitsAdjust = ModUnitsAdjust_temperature

dec_mode = "DJF"
annual_strict = False
drop_incomplete_djf = True
regrid = False
plot = True
netcdf = True
generate_sftlf = True
msyear = 1960
meyear = 1970
osyear = 1976
oeyear = 2005
