# Settings for extremes driver

# These settings are required
vars = ["pr"]  # Choices are 'pr','tasmax', 'tasmin'
test_data_set = ["MIROC6"]
realization = ["r1i1p1f1"]
test_data_path = "/p/css03/esgf_publish/CMIP6/CMIP/MIROC/MIROC6/1pctCO2/r1i1p1f1/day/%(variable)/gn/v20191016/"
filename_template = "%(variable)_day_MIROC6_1pctCO2_r1i1p1f1_gn_*.nc"

metrics_output_path = "/home/ordonez4/pmp_results/drcdm/test/"

# Note: You can use the following placeholders in file templates:
# %(variable) to substitute variable name from "vars" (except in sftlf filenames)
# %(model) to substitute model name from "test_data_set"
# %(realization) to substitute realization from "realization"

# Optional settings
# See the README for more information about these settings
case_id = "test"
# sftlf_filename_template = '/p/css03/esgf_publish/CMIP6/CMIP/MIROC/MIROC6/piControl/r1i1p1f1/fx/sftlf/gn/v20190311/sftlf_fx_MIROC6_piControl_r1i1p1f1_gn.nc'

ModUnitsAdjust = (
    True,
    "multiply",
    86400.0,
    "mm/day",
)  # Convert model units from kg/m2/s to mm/day
dec_mode = "DJF"
annual_strict = False
drop_incomplete_djf = True
regrid = False
plots = False
generate_sftlf = True
msyear = 3300
meyear = 3349
