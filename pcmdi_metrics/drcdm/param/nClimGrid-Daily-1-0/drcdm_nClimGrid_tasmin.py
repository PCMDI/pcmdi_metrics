# Settings for extremes driver

# These settings are required
vars = ["tasmin"]  # Choices are 'pr','tasmax', 'tasmin'
test_data_set = ["Reference"]
realization = ["nClimGrid-Daily-1-0"]
test_data_path = "/pscratch/sd/a/aordonez/nclim/tasmin/"
filename_template = "tasmin_day_nClimGrid-Daily-1-0_PCMDI_5km_*.nc"

metrics_output_path = (
    "/pscratch/sd/a/aordonez/pmp_data/drcdm/obs/tasmin/nClimGrid-Daily-1-0/"
)


ModUnitsAdjust = (True, "KtoF", 0, "F")
dec_mode = "DJF"
annual_strict = False
drop_incomplete_djf = False
regrid = False
plot = True
netcdf = True
generate_sftlf = True
msyear = 1985
meyear = 2014
