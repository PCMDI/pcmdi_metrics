import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip5'
# exp = 'piControl'
exp = 'historical'
frequency = 'mo'
realm = 'atm'

# =================================================
# Analysis Options
# -------------------------------------------------
variability_mode = 'PNA'  # Available domains: NAM, NAO, SAM, PNA, PDO
seasons = ['DJF', 'MAM', 'JJA', 'SON']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

RemoveDomainMean = True  # Remove Domain Mean from each time step (default=True)
EofScaling = False  # Convert EOF pattern as unit variance (default=False)
landmask = False  # Maskout land region thus consider only ocean grid (default=False)

ConvEOF = True  # Calculate conventioanl EOF for model
CBF = True  # Calculate Common Basis Function (CBF) for model

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = True  # False
debug = False  # False

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = 'ERA20C'
reference_data_path = os.path.join(
    '/p/user_pub/PCMDIobs/PCMDIobs2/atmos/mon/psl/ERA-20C/gn/v20200707',
    'psl_mon_ERA-20C_BE_gn_v20200707_190001-201012.nc')

varOBS = 'psl'
ObsUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa; or (False, 0, 0)

osyear = 1900
oeyear = 2005
eofn_obs = 1

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/v20200116',
    '%(mip)/%(exp)/atmos/mon/%(variable)',
    '%(mip).%(exp).%(model).%(realization).mon.%(variable).xml')

modnames = ['ACCESS1-0', 'ACCESS1-3', 'BCC-CSM1-1', 'BCC-CSM1-1-M', 'BNU-ESM',
            'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CESM1-WACCM',
            'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CNRM-CM5-2', 'CSIRO-Mk3-6-0',
            'EC-EARTH', 'FGOALS-g2', 'FGOALS-s2', 'FIO-ESM', 'FIO-ESM',
            'GFDL-CM2p1', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M',
            'GISS-E2-H', 'GISS-E2-H-CC', 'GISS-E2-R', 'GISS-E2-R-CC',
            'HadCM3', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES',
            'INMCM4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR',
            'MIROC-ESM', 'MIROC-ESM-CHEM', 'MIROC4h', 'MIROC5',
            'MPI-ESM-LR', 'MPI-ESM-MR', 'MPI-ESM-P', 'NorESM1-M', 'NorESM1-ME']

modnames = ['all']
# modnames = ['ACCESS1-0']

realization = '*'  # realizations
# realization = 'r1i1p1'

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
    pmprdir = '/work/lee1043/imsi/result_test'

results_dir = os.path.join(
    pmprdir,
    '%(output_type)', 'variability_modes',
    '%(mip)', '%(exp)',
    '%(case_id)',
    '%(variability_mode)', '%(reference_data_name)')

nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics
