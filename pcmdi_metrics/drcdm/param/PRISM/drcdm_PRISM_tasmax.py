# Settings for extremes driver

# These settings are required
vars = ["tasmax"]  # Choices are 'pr','tasmax', 'tasmin'
test_data_set = ["Reference"]
realization = ["PRISM-M3"]
test_data_path = "/pscratch/sd/l/lee1043/obs4MIPs/OSU/PRISM-M3/day/tasmax/gn/latest/"
filename_template = "tasmax_day_PRISM-M3_PCMDI_gn_*.nc"

metrics_output_path = "/pscratch/sd/a/aordonez/pmp_data/drcdm/obs/tasmax/PRISM_2025/"


ModUnitsAdjust = (True, "CtoF", 0, "F")
dec_mode = "DJF"
annual_strict = False
drop_incomplete_djf = False
regrid = False
plot = True
netcdf = True
generate_sftlf = True
msyear = 1985
meyear = 2014
