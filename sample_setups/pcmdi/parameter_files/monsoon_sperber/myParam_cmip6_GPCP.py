import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = "cmip6"
exp = "historical"
frequency = "day"
realm = "atm"

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = "GPCP-1-3"
reference_data_path = "/p/user_pub/PCMDIobs/PCMDIobs2.0/atmos/day/pr/GPCP-1-3/gn/v20190225/pr_day_GPCP-1-3_BE_gn_19961002-20170101.nc"  # noqa
reference_data_lf_path = (
    "/work/lee1043/DATA/LandSeaMask_1x1_NCL/NCL_LandSeaMask_rewritten.nc"  # noqa
)

varOBS = "pr"
ObsUnitsAdjust = (True, "multiply", 86400.0)  # kg m-2 s-1 to mm day-1

osyear = 1996
oeyear = 2016

includeOBS = True

# =================================================
# Models
# -------------------------------------------------
modpath = "/work/lee1043/ESGF/xmls/%(mip)/historical/day/pr/%(mip).%(model).%(exp).%(realization).day.pr.xml"
# modpath_lf = '/work/lee1043/ESGF/xmls/cmip5/historical/fx/sftlf/cmip5.%(model).historical.r0i0p0.fx.sftlf.xml'
modpath_lf = (
    "/work/lee1043/ESGF/CMIP6/CMIP/%(model)/sftlf_fx_%(model)_historical_r1i1p1f2_gr.nc"
)

# modnames = ['ACCESS1-0', 'ACCESS1-3', 'BCC-CSM1-1', 'BCC-CSM1-1-M', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'EC-EARTH', 'FGOALS-g2', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H', 'GISS-E2-R', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 'INMCM4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC-ESM', 'MIROC-ESM-CHEM', 'MIROC4h', 'MIROC5', 'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'MRI-ESM1', 'NorESM1-M']  # noqa

# modnames = ['ACCESS1-0']
modnames = ["CNRM-CM6-1"]

realization = "r1i1p1f2"
# realization = '*'

varModel = "pr"
ModUnitsAdjust = (True, "multiply", 86400.0)  # kg m-2 s-1 to mm day-1
units = "mm/d"

msyear = 1961
meyear = 1999

# =================================================
# Output
# -------------------------------------------------
# case_id = "{:v%Y%m%d-%H%M}".format(datetime.datetime.now())
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
# results_dir = '/work/lee1043/imsi/result_test/%(output_type)/monsoon/monsoon_sperber/'+case_id
results_dir = os.path.join(
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2",
    "%(output_type)",
    "monsoon",
    "monsoon_sperber",
    mip,
    exp,
    case_id,
    reference_data_name,
)
nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = True
debug = False
