import datetime
import glob
import os


def find_latest(path):
    dir_list = [p for p in glob.glob(path+"/v????????")]
    return sorted(dir_list)[-1]


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
variability_mode = 'PDO'  # Available domains: NAM, NAO, SAM, PNA, PDO
# seasons = ['monthly', 'yearly']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly
seasons = ['monthly']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

RemoveDomainMean = True  # Remove Domain Mean from each time step (default=True)
EofScaling = False  # Convert EOF pattern as unit variance (default=False)
landmask = True  # Maskout land region thus consider only ocean grid (default=False)

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
reference_data_name = 'HadISSTv1.1'
reference_data_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'
# reference_data_path = os.path.join(
#    '/p/user_pub/PCMDIobs/PCMDIobs2/atmos/mon/ts/HadISST-1-1/gn/v20200707',
#    'ts_mon_HadISST-1-1_BE_gn_v20200707_187001-201907.nc')

varOBS = 'sst'
# varOBS = 'ts'
ObsUnitsAdjust = (False, 0, 0)  # degC
# ObsUnitsAdjust = (True, 'subtract', 273.15)  # degK to degC

osyear = 1900
oeyear = 2005
eofn_obs = 1

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    find_latest('/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest'),
    '%(mip)/%(exp)/atmos/mon/%(variable)',
    '%(mip).%(exp).%(model).%(realization).mon.%(variable).xml')

modpath_lf = os.path.join(
    find_latest('/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest'),
    '%(mip)/historical/atmos/fx/sftlf/%(mip).historical.%(model).r0i0p0.fx.sftlf.xml')

modnames = ['all']
# modnames = ['ACCESS1-0', 'ACCESS1-3']

realization = '*'  # realizations
# realization = 'r1i1p1f1'

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
    pmprdir = '/work/lee1043/imsi/result_test'

results_dir = os.path.join(
    pmprdir,
    '%(output_type)', 'variability_modes',
    '%(mip)', '%(exp)',
    '%(case_id)',
    '%(variability_mode)', '%(reference_data_name)')

nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics
