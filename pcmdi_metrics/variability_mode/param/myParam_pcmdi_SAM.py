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
variability_mode = "SAM"  # Available domains: NAM, NAO, SAM, PNA, PDO
seasons = [
    "DJF",
    "MAM",
    "JJA",
    "SON",
]  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

ConvEOF = True  # Calculate conventioanl EOF for model
CBF = True  # Calculate Common Basis Function (CBF) for model

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = False
debug = False

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = "NOAA-CIRES_20CR"
reference_data_path = os.path.join(
    "/p/user_pub/PCMDIobs/obs4MIPs/NOAA-ESRL-PSD/20CR/mon/psl/gn/latest",
    "psl_mon_20CR_PCMDI_gn_187101-201212.nc"
    # "/p/user_pub/PCMDIobs/PCMDIobs2/atmos/mon/psl/20CR/gn/v20200707",
    # "psl_mon_20CR_BE_gn_v20200707_187101-201212.nc",
)

varOBS = "psl"
ObsUnitsAdjust = (True, "divide", 100.0)  # Pa to hPa; or (False, 0, 0)

osyear = 1955
oeyear = 2005

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    find_latest("/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest"),
    "%(mip)/%(exp)/atmos/mon/%(variable)",
    "%(mip).%(exp).%(model).%(realization).mon.%(variable).xml",
)

modnames = ["all"]

realization = "*"

varModel = "psl"
ModUnitsAdjust = (True, "divide", 100.0)  # Pa to hPa

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
