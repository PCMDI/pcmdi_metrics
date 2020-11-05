import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip5'
exp = 'historical'
frequency = 'mo'
realm = 'atm'

# =================================================
# Analysis Options
# -------------------------------------------------
variability_mode = 'PDO'  # Available domains: NAM, NAO, SAM, PNA, PDO
seasons = ['monthly']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

landmask = True  # Maskout land region thus consider only ocean grid (default=False)

ConvEOF = True  # Calculate conventioanl EOF for model
CBF = True  # Calculate Common Basis Function (CBF) for model

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = True  # False
debug = True  # False

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = 'HadISSTv1.1'
reference_data_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'

varOBS = 'sst'
ObsUnitsAdjust = (False, 0, 0)  # degC

osyear = 1900
oeyear = 2005
eofn_obs = 1

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    '/p/css03/cmip5_css02/data/cmip5/output1/CSIRO-BOM/ACCESS1-0/historical/mon/atmos/Amon/r1i1p1/ts/1/',
    'ts_Amon_ACCESS1-0_historical_r1i1p1_185001-200512.nc')

modpath_lf = os.path.join(
    '/p/css03/cmip5_css02/data/cmip5/output1/CSIRO-BOM/ACCESS1-0/amip/fx/atmos/fx/r0i0p0/sftlf/1/',
    'sftlf_fx_ACCESS1-0_amip_r0i0p0.nc')

modnames = ['ACCESS1-0']

realization = 'r1i1p1'

varModel = 'ts'
ModUnitsAdjust = (True, 'subtract', 273.15)  # degK to degC

msyear = 1900
meyear = 2005
eofn_mod = 1

# =================================================
# Output
# -------------------------------------------------
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmprdir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2'

if debug:
    pmprdir = '/work/lee1043/temporary/result_test'

results_dir = os.path.join(
    pmprdir,
    '%(output_type)', 'variability_modes',
    '%(mip)', '%(exp)',
    '%(case_id)',
    '%(variability_mode)', '%(reference_data_name)')

nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics
