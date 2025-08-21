# Settings for extremes driver
# These settings are required
vars = ["pr", "tasmax", "tasmin"]  # Choices are 'pr','tasmax', 'tasmin', "tas"
test_data_set = ["MIROC6", "ACCESS-CM2", "GFDL-CM4", "EC-Earth3"]

# heat_index_t_var =  ['tasmax'] # dewpoint
# heat_index_td_var =  ['tasmax']
realization = ["r1i1p1f1"]
# test_data_path = "/pscratch/sd/j/jsgoodni/testData/"
# test_data_path = "/global/cfs/projectdirs/m3522/datalake/LOCA2/ACCESS-CM2/0p0625deg/r1i1p1f1/historical/%(variable)/"
# 0413 # 0519
test_data_path = "/global/cfs/projectdirs/m3522/datalake/LOCA2/%(model)/0p0625deg/r1i1p1f1/historical/%(variable)/"
filename_template = (
    "%(variable).%(model).historical.r1i1p1f1.1950-2014.LOCA_16thdeg_v2022????.nc"
)
# metrics_output_path = "/pscratch/sd/j/jsgoodni/pmp_results/drcdm/LOCA2/"
metrics_output_path = (
    "/pscratch/sd/j/jsgoodni/pmp_results/drcdm/LOCA2/MultipleModelTest_TX/"
)

# Note: You can use the following placeholders in file templates:
# %(variable) to substitute variable name from "vars" (except in sftlf filenames)
# %(model) to substitute model name from "test_data_set"
# %(realization) to substitute realization from "realization"

# Optional settings
# See the README for more information about these settings
# case_id = "test_pr"
# 1976 - 2005
# reference_data_path = "/pscratch/sd/j/jsgoodni/testData/"
# reference_data_set = ["Livneh"]
reference_filename_template = (
    None  # "%(variable).Livneh.historical.r1i1p1f1.1950-2014.v20250602.nc"
)

# Heat Index Section
# Sub-daily (ideally hourly) data must be provided to ensure proper max heat index calculation

shp_path = "/pscratch/sd/j/jsgoodni/shapefiles/cb_2018_us_state_20m.shp"
attribute = "NAME"
region_name = "Texas"  # Region name within the shapefile
# coords = ['latitude', 'longitude']
# sftlf_filename_template = '/p/css03/esgf_publish/CMIP6/CMIP/MIROC/MIROC6/piControl/r1i1p1f1/fx/sftlf/gn/v20190311/sftlf_fx_MIROC6_piControl_r1i1p1f1_gn.nc'

ModUnitsAdjust_precip = (
    True,
    "multiply",
    86400.0 / 25.4,
    "inches",
)  # Convert model units from kg/m2/s to mm/day
ObsUnitsAdjust_precip = (True, "multiply", 86400.0 / 25.4, "inches")

ModUnitsAdjust_temperature = (True, "KtoF", 0, "F")  # Set to False to Leave in K
ObsUnitsAdjust_temperature = (True, "CtoF", 0, "F")

ModUnitsAdjust = {
    v: ModUnitsAdjust_precip if "pr" in v else ModUnitsAdjust_temperature for v in vars
}
ObsUnitsAdjust = {
    v: ObsUnitsAdjust_precip if "pr" in v else ObsUnitsAdjust_temperature for v in vars
}

custom_thresholds = {  # accepted units - degF, degC, degK (temp), mm, inches (precip)
    "tasmin_ge": {"values": [60, 70, 80], "units": "degF"},
    "tasmin_le": {"values": [0, 32, 45], "units": "degF"},
    "tasmax_ge": {"values": [85, 90, 95, 100], "units": "degF"},
    "tasmax_le": {"values": [45], "units": "degF"},
    "growing_season": {"values": [32], "units": "degF"},
    "pr_ge": {"values": [1, 2, 3, 4], "units": "inches"},
}

dec_mode = "DJF"
annual_strict = False
exclude_leap = True
compute_tasmean = True
drop_incomplete_djf = False
regrid = False
plot = True
netcdf = True
generate_sftlf = True
msyear = 2000
meyear = 2010
osyear = 2000  # if no obs files provided, needs to be a subset of model year range
oeyear = 2010
