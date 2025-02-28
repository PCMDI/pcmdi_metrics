# Settings for extremes driver

# These settings are required
vars = ["pr"]  # Choices are 'pr','tasmax', 'tasmin'
test_data_set = ["Reference"]
realization = ["livneh-unsplit"]
test_data_path = "/pscratch/sd/a/aordonez/livneh/"
filename_template = "pr_day_livneh-unsplit-1-0_PCMDI_5km_*.nc"

metrics_output_path = "/pscratch/sd/a/aordonez/pmp_data/drcdm/obs/pr/livneh-unsplit/"

ModUnitsAdjust = (
    True,
    "multiply",
    86400.0,
    "mm/day",
)
dec_mode = "DJF"
annual_strict = False
drop_incomplete_djf = False
regrid = False
plot = True
netcdf = True
generate_sftlf = True
msyear = 1985
meyear = 2014
