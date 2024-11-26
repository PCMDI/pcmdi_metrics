#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# LIST OF MODEL VERSIONS TO BE TESTED

#  trouble model ICON-ESM-LR'

modnames = [
    "ACCESS-CM2",
    "ACCESS-ESM1-5",
    "AWI-ESM-1-1-LR",
    "BCC-CSM2-MR",
    "BCC-ESM1",
    "CAMS-CSM1-0",
    "CanESM5",
    "CAS-ESM2-0",
    "CESM2",
    "CESM2-WACCM",
    "CIESM",
    "CMCC-ESM2",
    "E3SM-1-0",
    "E3SM-1-1",
    "E3SM-2-0",
    "EC-Earth3",
    "FGOALS-f3-L",
    "GFDL-CM4",
    "GFDL-ESM4",
    "GISS-E2-1-G",
    "GISS-E2-1-H",
    "IPSL-CM5A2-INCA",
    "IPSL-CM6A-LR",
    "KIOST-ESM",
    "MIROC6",
    "MPI-ESM1-2-LR",
    "MRI-ESM2-0",
    "NESM3",
    "NorESM2-LM",
    "TaiESM1",
]


# ROOT PATH FOR MODELS CLIMATOLOGIES
test_data_path = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip6/historical/v20230823/pr/cmip6.historical.%(model).r1i1p1f1.mon.pr.198101-200512.AC.v20230823.nc"

# ROOT PATH FOR OBSERVATIONS
reference_data_path = "/p/user_pub/PCMDIobs/obs4MIPs_legacy/PCMDIobs2_clims/atmos/pr/TRMM-3B43v-7/pr_mon_TRMM-3B43v-7_BE_gn_199801-201712.v20200421.AC.nc"

# DIRECTORY WHERE TO PUT RESULTS
results_dir = "$OUTPUT_DIR$/monsoon_wang"

# Threshold
threshold = 2.5 / 86400

# monsoon domain mask based on observations
obs_mask = True
