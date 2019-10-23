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
variability_mode = 'NPGO'  # Available domains: NAM, NAO, SAM, PNA, PDO
# seasons = ['monthly', 'yearly']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly
seasons = ['monthly']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

RemoveDomainMean = True  # Remove Domain Mean from each time step (default=True)
EofScaling = False  # Convert EOF pattern as unit variance (default=False)
landmask = True  # Maskout land region thus consider only ocean grid (default=False)

ConvEOF = True  # Calculate conventioanl EOF for model
CBF = True  # Calculate Common Basis Function (CBF) for model

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = 'HadISSTv1.1'
reference_data_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'

varOBS = 'sst'
ObsUnitsAdjust = (False, 0, 0)  # degC

osyear = 1900
oeyear = 2005
eofn_obs = 2

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    '/work/lee1043/ESGF/xmls/%(mip)/%(exp)/mon/%(variable)',
    '%(mip).%(model).%(exp).%(realization).mon.%(variable).xml')

modpath_lf = '/work/lee1043/ESGF/xmls/%(mip)/historical/fx/sftlf/%(mip).%(model).historical.r0i0p0.fx.sftlf.xml'

modnames = ['all']

# modnames = ['ACCESS1-0', 'ACCESS1-3']

realization = '*'  # realizations
# realization = 'r1i1p1f1'

varModel = 'ts'
ModUnitsAdjust = (True, 'subtract', 273.15)  # degK to degC

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
