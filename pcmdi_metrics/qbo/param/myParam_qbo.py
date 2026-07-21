import datetime

# =================================================
# Background Information
# -------------------------------------------------
mip_era = "CMIP6"
# mip_era = "CMIP5"

mip = mip_era.lower()

exps = ["historical"]
# exps = ["ssp126", "ssp245", "ssp375", "ssp585"]
# exps = ["ssp370"]

# =================================================
# Miscellaneous
# -------------------------------------------------
debug = False
# debug = True

#
# parallel
#
parallel = False
# parallel = True  # not complete yet ... working on it!

num_processes = 10
# num_processes = 3

# =================================================
# Reference
# -------------------------------------------------
reference_name = "ERA5"

# ref_input_file = "/work/lee1043/DATA/ERA5/ERA5_u50_monthly_1979-2021.nc"
ref_input_file = "/work/lee1043/DATA/ERA5/ERA5_u50_monthly_1979-2021_rewrite.nc"
# ref_input_file2 = "/work/lee1043/DATA/ERA5/ERA5_olr_daily_40s40n_1979-2021.nc"
ref_input_file2 = "/work/lee1043/DATA/ERA5/ERA5_olr_daily_40s40n_1979-2021_rewrite.nc"

ref_var1 = "u50"
ref_level1 = None  # hPa (=mb)

ref_var2 = "olr"

ref_start = "1979-01"
ref_end = "2005-12"
# ref_end = "2021-12"

include_reference = True
# include_reference = False

# =================================================
# Models
# -------------------------------------------------
# models = "all"
# models = ["ACCESS-CM2"]
models = []

# first_member_only = True
first_member_only = False

# Input 1: u50 monthly
var1 = "ua"
freq1 = "mon"
cmipTable1 = "Amon"
level1 = 50  # hPa

# Input 2: olr daily
var2 = "rlut"
freq2 = "day"
cmipTable2 = "day"

# =================================================
# Output
# -------------------------------------------------
result_dir = "output"
if parallel:
    result_dir = "output_parallel"
if debug:
    result_dir = "output_debug"

# Output: diagnostics --- netcdf file
output_filename_template = "qbo_mjo_%(model)_%(exp)_%(realization)_%(start)_%(end).nc"

overwrite_output = False

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())

#
# Processing options
#
regrid = True
regrid_tool = "xesmf"
target_grid = "2x2"

taper_to_mean = True
