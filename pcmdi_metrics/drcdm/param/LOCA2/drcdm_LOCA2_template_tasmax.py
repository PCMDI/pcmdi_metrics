# Settings for extremes driver

# These settings are required
vars = ["tasmax"]  # Choices are 'pr','tasmax', 'tasmin'
test_data_path = "/global/cfs/projectdirs/m3522/cmip6/LOCA2/%(model)/0p0625deg/%(realization)/historical/tasmax/"
filename_template = "tasmax.%(model).historical.*.LOCA_16thdeg_*.nc"


ModUnitsAdjust=(True, 'KtoF', 0, 'F')
dec_mode = "DJF"
annual_strict = False
drop_incomplete_djf = False
regrid = False
plot = True
netcdf = True
generate_sftlf = False
msyear = 1985
meyear = 2014
