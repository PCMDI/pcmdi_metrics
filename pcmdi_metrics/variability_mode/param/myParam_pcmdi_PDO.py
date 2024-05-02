import datetime
import glob
import os


def find_latest(path):
    dir_list = [p for p in glob.glob(path + "/v????????")]
    return sorted(dir_list)[-1]


# =================================================
# Background Information
# -------------------------------------------------
mip = "cmip5"
exp = "historical"
frequency = "mo"
realm = "atm"

# =================================================
# Analysis Options
# -------------------------------------------------
variability_mode = "PDO"  # Available domains: NAM, NAO, SAM, PNA, PDO
seasons = ["monthly"]  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

landmask = True  # Maskout land region thus consider only ocean grid (default=False)

ConvEOF = True  # Calculate conventioanl EOF for model
CBF = True  # Calculate Common Basis Function (CBF) for model

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = False  # False
debug = False  # False

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = "HadISSTv1.1"
reference_data_path = (
    # "/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc"  # original data source
    "/p/user_pub/PCMDIobs/obs4MIPs/MOHC/HadISST-1-1/mon/ts/gn/v20210727/ts_mon_HadISST-1-1_PCMDI_gn_187001-201907.nc"  # obs4MIPs data
)

# varOBS = "sst"
# ObsUnitsAdjust = (False, 0, 0)  # degC
varOBS = "ts"
ModUnitsAdjust = (True, "subtract", 273.15)  # degK to degC

osyear = 1900
oeyear = 2005

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    find_latest("/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest"),
    "%(mip)/%(exp)/atmos/mon/%(variable)",
    "%(mip).%(exp).%(model).%(realization).mon.%(variable).xml",
)

modpath_lf = os.path.join(
    find_latest("/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest"),
    "%(mip)/%(exp)/atmos/fx/sftlf",
    "%(mip).%(exp).%(model).r0i0p0.fx.sftlf.xml",
)

modnames = ["all"]

realization = "*"

varModel = "ts"
ModUnitsAdjust = (True, "subtract", 273.15)  # degK to degC

msyear = 1900
meyear = 2005

# =================================================
# Output
# -------------------------------------------------
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmprdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"

if debug:
    pmprdir = "/work/lee1043/temporary/result_test"

results_dir = os.path.join(
    pmprdir,
    "%(output_type)",
    "variability_modes",
    "%(mip)",
    "%(exp)",
    "%(case_id)",
    "%(variability_mode)",
    "%(reference_data_name)",
)

# Output for obs
plot_obs = True  # Create map graphics
nc_out_obs = True  # Write output in NetCDF

# Output for models
nc_out = True
plot = True
