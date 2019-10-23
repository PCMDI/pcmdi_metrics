import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip6'
# exp = 'piControl'
exp = 'historical'
frequency = 'mo'
realm = 'atm'

# =================================================
# Analysis Options
# -------------------------------------------------
variability_mode = 'NPO'  # Available domains: NAM, NAO, SAM, PNA, PDO
seasons = ['DJF', 'MAM', 'JJA', 'SON', 'monthly']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

RemoveDomainMean = True  # Remove Domain Mean from each time step (default=True)
EofScaling = False  # Convert EOF pattern as unit variance (default=False)
landmask = False  # Maskout land region thus consider only ocean grid (default=False)

ConvEOF = True  # Calculate conventioanl EOF for model
CBF = True  # Calculate Common Basis Function (CBF) for model

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = 'NOAA-CIRES_20CR'
reference_data_path = os.path.join(
    '/p/user_pub/PCMDIobs/PCMDIobs2.0/atmos/mon/psl/20CR/gn/v20190221',
    'psl_mon_20CR_BE_gn_187101-201212.nc')

varOBS = 'psl'
ObsUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa; or (False, 0, 0)

osyear = 1900
oeyear = 2005
eofn_obs = 2

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    '/work/lee1043/ESGF/xmls/%(mip)/%(exp)/mon/%(variable)',
    '%(mip).%(model).%(exp).%(realization).mon.%(variable).xml')

modnames = ['all']
# modnames = ['IPSL-CM6A-LR']

realization = '*'  # realizations
# realization = 'r1i1p1f1'

varModel = 'psl'
ModUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa

msyear = 1900
meyear = 2005
eofn_mod = 2

# =================================================
# Output
# -------------------------------------------------
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
results_dir = os.path.join(
    '/p/user_pub/pmp/pmp_results/pmp_v1.1.2',
    '%(output_type)/variability_modes/%(mip)/%(exp)',
    case_id,
    '%(variability_mode)/%(reference_data_name)')
nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = True  # False
debug = False  # False
