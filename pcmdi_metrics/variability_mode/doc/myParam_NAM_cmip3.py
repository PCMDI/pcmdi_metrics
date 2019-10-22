import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip3'
exp = '20c3m'
frequency = 'mo'
realm = 'atm'

# =================================================
# Analysis Options
# -------------------------------------------------
variability_mode = 'NAM'  # Available domains: NAM, NAO, SAM, PNA, PDO
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
reference_data_path = '/p/user_pub/PCMDIobs/PCMDIobs2.0/atmos/mon/psl/20CR/gn/v20190221/psl_mon_20CR_BE_gn_187101-201212.nc'

varOBS = 'psl'
ObsUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa; or (False, 0, 0)

osyear = 1900
oeyear = 2005
eofn_obs = 1

# =================================================
# Models
# -------------------------------------------------
modpath = '/work/lee1043/ESGF/xmls/%(mip)/%(exp)/mon/%(variable)/%(variable).%(model).%(realization).xml'

modnames = [
    'bcc_cm1',
    'bccr_bcm2_0',
    'cccma_cgcm3_1',
    'cccma_cgcm3_1_t63',
    'cnrm_cm3',
    'csiro_mk3_0',
    'csiro_mk3_5',
    'gfdl_cm2_0',
    'gfdl_cm2_1',
    'giss_aom',
    'giss_model_e_h',
    'giss_model_e_r',
    'iap_fgoals1_0_g',
    'ingv_echam4',
    'inmcm3_0',
    'ipsl_cm4',
    'miroc3_2_hires',
    'miroc3_2_medres',
    'miub_echo_g',
    'mpi_echam5',
    'mri_cgcm2_3_2a',
    'ncar_ccsm3_0',
    'ncar_pcm1',
    'ukmo_hadcm3',
    'ukmo_hadgem1'
]

modnames = [
    'bccr_bcm2_0',
    'cccma_cgcm3_1',
    'cccma_cgcm3_1_t63',
    'cnrm_cm3',
    'gfdl_cm2_0',
    'gfdl_cm2_1',
    'giss_aom',
    'giss_model_e_h',
    'giss_model_e_r',
    'iap_fgoals1_0_g',
    'ingv_echam4',
    'inmcm3_0',
    'ipsl_cm4',
    'miroc3_2_hires',
    'miroc3_2_medres',
    'miub_echo_g',
    'mpi_echam5',
    'mri_cgcm2_3_2a',
    'ukmo_hadcm3',
    'ukmo_hadgem1',
]

modnames = ['all']
# modnames = ['EC-EARTH']

realization = '*'  # realizations
# realization = 'run1'

varModel = 'psl'
ModUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa

msyear = 1900
meyear = 2005
eofn_mod = 1

# =================================================
# Output
# -------------------------------------------------
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
results_dir = os.path.join(
    '/p/user_pub/pmp/pmp_results/pmp_v1.1.2',
    #'/work/lee1043/imsi/result_test',
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
