# Settings for extremes driver
# These settings are required
# Variable - Heat Index

test_data_set = ["ACCESS-CM2-LOCA"]

# heat_index_t_var =  ['tasmax'] # dewpoint
# heat_index_td_var =  ['tasmax']
realization = ["r1i1p1f1"]
test_data_path = "/global/cfs/projectdirs/m3522/cmip6/LOCA2/ACCESS-CM2/0p0625deg/r1i1p1f1/historical/%(variable)/"
filename_template = (
    "%(variable).ACCESS-CM2.historical.r1i1p1f1.1950-2014.LOCA_16thdeg_v20240915.nc"
)
# metrics_output_path = "/pscratch/sd/j/jsgoodni/pmp_results/drcdm/LOCA2/"
metrics_output_path = "/global/cfs/projectdirs/m2637/jsgoodni/pmp_results/LOCA2/"

# Note: You can use the following placeholders in file templates:
# %(variable) to substitute variable name from "vars" (except in sftlf filenames)
# %(model) to substitute model name from "test_data_set"
# %(realization) to substitute realization from "realization"

# Optional settings
# See the README for more information about these settings
# case_id = "test_pr"
# 1976 - 2005
# reference_data_path = "/pscratch/sd/j/jsgoodni/testData/pr_obs.nc"
# reference_data_set = ["GMFD"]
# reference_filename_template = "%(variable)_obs.nc"

# Heat Index Section
# Sub-daily (ideally hourly) data must be provided to ensure proper max heat index calculation

# shp_path = "/pscratch/sd/j/jsgoodni/shapefiles/cb_2018_us_state_20m.shp"
# attribute = "NAME"
# region_name = "California" # Region name within the shapefile
# coords = ['latitude', 'longitude']
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
    ObsUnitsAdjust = ModUnitsAdjust_precip
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
msyear = 1985
meyear = 2015
osyear = 1976
oeyear = 2005
