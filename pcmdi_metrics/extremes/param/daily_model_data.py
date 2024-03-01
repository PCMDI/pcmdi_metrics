# This parameter file can be used as a guide
# for setting up the extremes parameter file.

# ====tasmax====
# vars = ["tasmax"]
# ModUnitsAdjust=(True,"subtract",273,"C")

# ===pr====
# Note: Variables do not have to be run separately
# if units do not require adjusting.
vars = ["pr"]
ModUnitsAdjust = (True, "multiply", 86400, "mm/day")


metrics_output_path = "./%(case_id)"

# Covariate - comment out to do nonstationary
# covariate = "mole_fraction_of_carbon_dioxide_in_air"
# covariate_path ="/home/ordonez4/git/pcmdi_metrics/pcmdi_metrics/extremes/co2_annual_1850-1999.nc"

# Model data settings
test_data_set = ["MRI-ESM2-0"]
realization = ["r1i1p1f1"]
test_data_path = "/p/user_pub/xclim/CMIP6/CMIP/1pctCO2/atmos/day/%(variable)"
filename_template = "CMIP6.CMIP.1pctCO2.*.%(model).%(realization).day.%(variable).atmos.*.v????????.0000000.0.xml"
sftlf_filename_template = "/p/css03/esgf_publish/CMIP6/CMIP/*/%(model)/piControl/r1i1p1f1/fx/sftlf/gn/v????????/sftlf_fx_%(model)_piControl_r1i1p1f1_gn.nc"

case_id = "demo"
dec_mode = "DJF"
annual_strict = False
drop_incomplete_djf = False
regrid = True
plots = False
generate_sftlf = True
msyear = 1980
meyear = 1999
return_period = 5

# Regional selection settings
# coords=""
# shp_path = ""
# column = ""
# region_name = ""

# Observational settings
reference_data_path = "/p/user_pub/PCMDIobs/obs4MIPs/NASA-JPL/GPCP-1-3/day/pr/gn/latest/pr_day_GPCP-1-3_PCMDI_gn_19961002-20170101.nc"
reference_data_set = "GPCP-1-3"
osyear = 1997
oeyear = 2016
ObsUnitsAdjust = (True, "multiply", 86400, "mm/day")
