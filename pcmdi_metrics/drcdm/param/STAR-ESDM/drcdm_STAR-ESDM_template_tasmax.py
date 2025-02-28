# Settings for extremes driver

# These settings are required
vars = ["tasmax"]  # Choices are 'pr','tasmax', 'tasmin'
test_data_path = "/global/cfs/projectdirs/m3522/project_downscale/CMIP6/NAM/TTU/STAR-ESDM-V1/%(model)/CMIP/historical/%(realization)/day/%(variable)/v20241130/"
filename_template = (
    "tasmax_NAM_CMIP6_%(model)_historical_%(realization)_TTU_STAR-ESDM-V1_day_*.nc"
)


ModUnitsAdjust = (True, "KtoF", 0, "F")
dec_mode = "DJF"
annual_strict = False
drop_incomplete_djf = False
regrid = False
plot = True
netcdf = True
generate_sftlf = False
msyear = 1985
meyear = 2014
