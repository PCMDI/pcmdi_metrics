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
variability_mode = 'NAM'  # Available domains: NAM, NAO, SAM, PNA, PDO
seasons = ['DJF']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

#RemoveDomainMean = True  # Remove Domain Mean from each time step (default=True)
#EofScaling = False  # Convert EOF pattern as unit variance (default=False)
#landmask = False  # Maskout land region thus consider only ocean grid (default=False)

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
reference_data_name = 'NOAA-CIRES_20CR'
reference_data_path = os.path.join(
    '/p/user_pub/PCMDIobs/PCMDIobs2/atmos/mon/psl/20CR/gn/v20200707',
    'psl_mon_20CR_BE_gn_v20200707_187101-201212.nc')

varOBS = 'psl'
ObsUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa; or (False, 0, 0)

osyear = 1900
oeyear = 2005
eofn_obs = 1

# =================================================
# Models
# -------------------------------------------------
#modpath = os.path.join(
#    '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/v20201031',
#    '%(mip)/%(exp)/atmos/mon/%(variable)',
#    '%(mip).%(exp).%(model).%(realization).mon.%(variable).xml')

modpath = os.path.join(
    '/p/css03/cmip5_css02/data/cmip5/output1/CSIRO-BOM/ACCESS1-0/historical/mon/atmos/Amon/r1i1p1/psl/1',
    'psl_Amon_ACCESS1-0_historical_r1i1p1_185001-200512.nc')

modnames = ['ACCESS1-0']

# realization = '*'  # realizations
realization = 'r1i1p1'

varModel = 'psl'
ModUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa

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
