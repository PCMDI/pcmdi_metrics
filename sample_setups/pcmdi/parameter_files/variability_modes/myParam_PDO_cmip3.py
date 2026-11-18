import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = "cmip3"
exp = "20c3m"
frequency = "mo"
realm = "atm"

# =================================================
# Analysis Options
# -------------------------------------------------
variability_mode = "PDO"  # Available domains: NAM, NAO, SAM, PNA, PDO
# seasons = ['monthly', 'yearly']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly
seasons = ["monthly"]  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

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
eofn_obs = 1

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/%(mip)/%(exp)",
    "%(variable).%(model).%(realization).xml",
)
modpath_lf = os.path.join(
    "/work/lee1043/ESGF/xmls/%(mip)/historical/fx/sftlf",
    "%(mip).%(model).historical.r0i0p0.fx.sftlf.xml",
)

modnames = [
    "bccr_bcm2_0",
    "cccma_cgcm3_1",
    "cccma_cgcm3_1_t63",
    "cnrm_cm3",
    "gfdl_cm2_0",
    "gfdl_cm2_1",
    "giss_aom",
    "giss_model_e_h",
    "giss_model_e_r",
    "iap_fgoals1_0_g",
    "ingv_echam4",
    "inmcm3_0",
    "ipsl_cm4",
    "miroc3_2_hires",
    "miroc3_2_medres",
    "miub_echo_g",
    "mpi_echam5",
    "mri_cgcm2_3_2a",
    "ukmo_hadcm3",
    "ukmo_hadgem1",
]

# modnames = ['giss_model_e_h']
modnames = ["all"]

realization = "*"  # realizations
# realization = 'run1'

varModel = "ts"
ModUnitsAdjust = (True, "subtract", 273.15)  # degK to degC

msyear = 1900
meyear = 2005
eofn_mod = 1

# =================================================
# Output
# -------------------------------------------------
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmprdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"

if debug:
    pmprdir = "/work/lee1043/imsi/result_test"

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

nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics
