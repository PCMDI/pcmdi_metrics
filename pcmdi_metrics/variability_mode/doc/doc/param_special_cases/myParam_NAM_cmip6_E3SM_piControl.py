import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip6'
exp = 'piControl'
#exp = 'historical'
frequency = 'mo'
realm = 'atm'

# =================================================
# Analysis Options
# -------------------------------------------------
variability_mode = 'NAM'  # Available domains: NAM, NAO, SAM, PNA, PDO
seasons = ['DJF', 'MAM', 'JJA', 'SON'] # Available seasons: DJF, MAM, JJA, SON, monthly, yearly
# seasons = ['DJF']
# seasons = ['monthly'] # Available seasons: DJF, MAM, JJA, SON, monthly, yearly
# seasons = ['yearly'] # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

RemoveDomainMean = True  # Remove Domain Mean from each time step (default=True)
EofScaling = False  # Convert EOF pattern as unit variance (default=False)
landmask = False # Maskout land region thus consider only ocean grid (default=False)

ConvEOF = True  # Calculate conventioanl EOF for model
CBF = True  # Calculate Common Basis Function (CBF) for model

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = 'NOAA-CIRES_20CR'
reference_data_path = '/work/lee1043/DATA/reanalysis/20CR/slp_monthly_mean/monthly.prmsl.1871-2012.nc'

varOBS = 'prmsl'
ObsUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa; or (False, 0, 0)

osyear = 1900
oeyear = 2005
eofn_obs = 1

# =================================================
# Models
# -------------------------------------------------
#modpath = '/work/lee1043/ESGF/xmls/%(mip)/historical/mon/%(variable)/%(mip).%(model).historical.%(realization).mon.%(variable).xml'
#modpath = '/work/lee1043/ESGF/CMIP6/CMIP/%(model)/piControl/%(mip).%(model).piControl.%(realization).mon.%(variable).nc'
modpath = '/work/lee1043/ESGF/E3SM/piControl/%(mip).%(model).piControl.%(realization).mon.%(variable).nc'

#modnames = ['all']
#modnames = ['GFDL-CM4']
modnames = ['E3SM']

realization = '*' # realizations
# realization = 'r1i1p1f1'

varModel = 'psl'
ModUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa

msyear = 1900
meyear = 2005
eofn_mod = 1

# =================================================
# Output
# -------------------------------------------------
#case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
results_dir = os.path.join(
    #'/p/user_pub/pmp/pmp_results/pmp_v1.1.2',
    '/work/lee1043/cdat/pmp/variability_mode/cmip6_E3SM_result',
    '%(output_type)', 'variability_modes',
    mip, exp, case_id, variability_mode)
nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = True  # False
debug = False  # False
