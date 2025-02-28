# Settings for drcdm driver

# Note: make sure you know whether the precip version you are using is LOCA2-1
# or LOCA2-0. I believe 20220519 is LOCA2-1 but confirm before using.
vars = ["pr"]  # Choices are 'pr','tasmax', 'tasmin'
test_data_path = "/global/cfs/projectdirs/m3522/cmip6/LOCA2/%(model)/0p0625deg/%(realization)/historical/pr/"
filename_template = "pr.%(model).historical.*.LOCA_16thdeg_v20220519.nc"


ModUnitsAdjust = (
    True,
    "multiply",
    86400.0,
    "mm/day",
)
dec_mode = "JFD"  # Use JFD to match Tempest Extremes results
annual_strict = False  # This only matters for 5-day values
drop_incomplete_djf = False  # False to match Tempest Extremes
regrid = False
plot = True
netcdf = True
generate_sftlf = False
msyear = 1985
meyear = 2014
