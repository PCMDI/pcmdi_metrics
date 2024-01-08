import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = "cmip5"
exp = "historical"
frequency = "da"
realm = "atm"

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = False
debug = False

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = "GPCP-1-3"
reference_data_path = "/p/user_pub/PCMDIobs/PCMDIobs2/atmos/day/pr/GPCP-1-3/gn/v20200924/pr_day_GPCP-1-3_BE_gn_v20200924_19961002-20170101.nc"  # noqa
reference_data_lf_path = (
    "/work/lee1043/DATA/LandSeaMask_1x1_NCL/NCL_LandSeaMask_rewritten.nc"  # noqa
)

varOBS = "pr"
ObsUnitsAdjust = (True, "multiply", 86400.0)  # kg m-2 s-1 to mm day-1

osyear = 2000 #1996
oeyear = 2002 #2016

includeOBS = True

# =================================================
# Models
# -------------------------------------------------
modpath = "/work/lee1043/ESGF/xmls/cmip5/historical/day/pr/cmip5.%(model).%(exp).%(realization).day.pr.xml"
modpath_lf = "/work/lee1043/ESGF/xmls/cmip5/historical/fx/sftlf/cmip5.%(model).historical.r0i0p0.fx.sftlf.xml"

# modnames = ['ACCESS1-0', 'ACCESS1-3', 'BCC-CSM1-1', 'BCC-CSM1-1-M', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'EC-EARTH', 'FGOALS-g2', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H', 'GISS-E2-R', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 'INMCM4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC-ESM', 'MIROC-ESM-CHEM', 'MIROC4h', 'MIROC5', 'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'MRI-ESM1', 'NorESM1-M']  # noqa

modnames = ["ACCESS1-0"]

realization = "r1i1p1"
# realization = '*'

varModel = "pr"
ModUnitsAdjust = (True, "multiply", 86400.0)  # kg m-2 s-1 to mm day-1
units = "mm/d"

msyear = 2000 #1961
meyear = 2002 #1999

# =================================================
# Output
# -------------------------------------------------
#pmprdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"
#pmprdir = "/p/user_pub/climate_work/dong12/pmp_monsoon_result"
pmprdir = "/home/dong12/PMP/pcmdi_metrics/doc/jupyter/Demo/demo_output/monsoon_sperber/Ex1"
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())

if debug:
    pmprdir = "/work/lee1043/imsi/result_test"
    case_id = "{:v%Y%m%d-%H%M}".format(datetime.datetime.now())

results_dir = os.path.join(
    pmprdir, "%(output_type)", "monsoon", "monsoon_sperber", mip, exp, case_id
)

nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics
