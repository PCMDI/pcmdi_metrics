import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# LIST OF MODEL VERSIONS TO BE TESTED
modnames = ['CanCM4']
modnames = ['CESM2']
#modnames = ['IPSL-CM6A-LR']
#modnames = ['ACCESS-CM2', 'ACCESS-ESM1-5', 'AWI-CM-1-1-MR', 'AWI-ESM-1-1-LR', 'BCC-CSM2-MR', 'BCC-ESM1', 'CAMS-CSM1-0', 'CanESM5-1', 'CanESM5', 'CAS-ESM2-0', 'CESM2-FV2', 'CESM2', 'CESM2-WACCM-FV2', 'CESM2-WACCM', 'CIESM', 'CMCC-CM2-HR4', 'CMCC-CM2-SR5', 'CMCC-ESM2', 'E3SM-1-0', 'E3SM-1-1-ECA', 'E3SM-1-1', 'E3SM-2-0', 'EC-Earth3-AerChem', 'EC-Earth3-CC', 'EC-Earth3', 'EC-Earth3-Veg-LR', 'EC-Earth3-Veg', 'FGOALS-f3-L', 'FIO-ESM-2-0', 'GFDL-CM4', 'GFDL-ESM4', 'GISS-E2-1-G-CC', 'GISS-E2-1-G', 'GISS-E2-1-H', 'GISS-E2-2-G', 'GISS-E2-2-H', 'ICON-ESM-LR', 'INM-CM4-8', 'INM-CM5-0', 'IPSL-CM5A2-INCA', 'IPSL-CM6A-LR-INCA', 'IPSL-CM6A-LR', 'KACE-1-0-G', 'KIOST-ESM', 'MCM-UA-1-0', 'MIROC6', 'MPI-ESM-1-2-HAM', 'MPI-ESM1-2-HR', 'MPI-ESM1-2-LR', 'MRI-ESM2-0', 'NESM3', 'NorCPM1', 'NorESM2-LM', 'NorESM2-MM', 'SAM0-UNICON', 'TaiESM1']

#  trouble model ICON-ESM-LR'


#cmip6 models
modnames = ['ACCESS-CM2', 'ACCESS-ESM1-5', 'AWI-ESM-1-1-LR', 'BCC-CSM2-MR', 'BCC-ESM1', 'CAMS-CSM1-0', 'CanESM5', 'CAS-ESM2-0', 'CESM2', 'CESM2-WACCM', 'CIESM', 'CMCC-ESM2', 'E3SM-1-0', 'E3SM-1-1', 'E3SM-2-0', 'EC-Earth3', 'FGOALS-f3-L', 'GFDL-CM4', 'GFDL-ESM4', 'GISS-E2-1-G', 'GISS-E2-1-H', 'IPSL-CM5A2-INCA', 'IPSL-CM6A-LR', 'KIOST-ESM', 'MIROC6', 'MPI-ESM1-2-LR', 'MRI-ESM2-0', 'NESM3', 'NorESM2-LM', 'TaiESM1']


#modnames = [ 'IPSL-CM5A2-INCA', 'IPSL-CM6A-LR', 'KIOST-ESM', 'MIROC6', 'MPI-ESM1-2-LR', 'MRI-ESM2-0', 'NESM3', 'NorESM2-LM', 'TaiESM1']

#cmip5 models
#modnames = [ACCESS1-0, BCC-CSM1-1-M, BNU-ESM, CanCM4, CanESM2, CCSM4, CESM1-BGC, CESM1-CAM5, CESM1-FASTCHEM, CESM1-WACCM, CMCC-CESM, CMCC-CM, CMCC-CMS, CNRM-CM5-2, CNRM-CM5, CSIRO-Mk3-6-0, FGOALS-g2, FIO-ESM, GFDL-CM2p1, GFDL-CM3, GFDL-ESM2G, GFDL-ESM2M, GISS-E2-H-CC, GISS-E2-H, GISS-E2-R-CC, GISS-E2-R, HadCM3, HadGEM2-AO, INMCM4, IPSL-CM5A-LR, IPSL-CM5A-MR, IPSL-CM5B-LR, MIROC4h, MIROC5, MIROC-ESM-CHEM, MIROC-ESM, MPI-ESM-LR, MPI-ESM-MR, MPI-ESM-P, MRI-CGCM3, MRI-ESM1, NorESM1-ME, NorESM1-M]

modnames = ['ACCESS1-0', 'BCC-CSM1-1-M', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-CAM5', 'CESM1-WACCM', 'CMCC-CESM', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'FGOALS-g2', 'FIO-ESM', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H', 'GISS-E2-R', 'HadCM3', 'HadGEM2-AO', 'INMCM4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC4h', 'MIROC5', 'MIROC-ESM', 'MPI-ESM-LR', 'MPI-ESM-MR', 'MRI-CGCM3', 'MRI-ESM1', 'NorESM1-M']

modnames = ['CMCC-CESM', "CNRM-CM5"]
modnames = ['ACCESS1-0', 'BCC-CSM1-1-M', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-CAM5', 'CESM1-WACCM', 'CMCC-CESM', 'CNRM-CM5', 'CSIRO-Mk3-6-0']
modnames = ['CESM1-WACCM', 'CMCC-CESM', 'CNRM-CM5', 'CSIRO-Mk3-6-0']
modnames = ['CNRM-CM5', 'CSIRO-Mk3-6-0', 'FGOALS-g2', 'FIO-ESM', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H', 'GISS-E2-R', 'HadCM3', 'HadGEM2-AO', 'INMCM4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC4h', 'MIROC5', 'MIROC-ESM', 'MPI-ESM-LR', 'MPI-ESM-MR', 'MRI-CGCM3', 'MRI-ESM1', 'NorESM1-M','ACCESS1-0', 'BCC-CSM1-1-M', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-CAM5', 'CESM1-WACCM', 'CMCC-CESM']

# ROOT PATH FOR MODELS CLIMATOLOGIES
#test_data_path = '$INPUT_DIR$/CMIP5_demo_clims/cmip5.historical.%(model).r1i1p1.mon.pr.198101-200512.AC.v20200426.nc'
#test_data_path = '/p/css03/cmip5_css02/data/cmip5/output1/CCCma/CanCM4/historical/mon/atmos/Amon/r1i1p1/pr/1/pr_Amon_CanCM4_historical_r1i1p1_196101-200512.nc' 

# cmip6
#test_data_path = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip6/historical/v20230823/pr/cmip6.historical.%(model).r1i1p1f1.mon.pr.198101-200512.AC.v20230823.nc'

# cmip5
test_data_path = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip5/historical/v20230323/pr/cmip5.historical.%(model).r1i1p1.mon.pr.198101-200512.AC.v20230323.nc'

# ROOT PATH FOR OBSERVATIONS
#reference_data_path = '$INPUT_DIR$/obs4MIPs_PCMDI_monthly/NOAA-NCEI/GPCP-2-3/mon/pr/gn/v20210727/pr_mon_GPCP-2-3_PCMDI_gn_197901-201907.nc'
#reference_data_path = '/p/user_pub/PCMDIobs/obs4MIPs/NASA-GSFC/GPCP-Monthly-3-2/mon/pr/gn/v20240408/pr_mon_GPCP-Monthly-3-2_RSS_gn_198301-198312.nc'
reference_data_path = '/p/user_pub/PCMDIobs/obs4MIPs_legacy/PCMDIobs2_clims/atmos/pr/TRMM-3B43v-7/pr_mon_TRMM-3B43v-7_BE_gn_199801-201712.v20200421.AC.nc'

# DIRECTORY WHERE TO PUT RESULTS
#results_dir = '$OUTPUT_DIR$/monsoon_wang'
results_dir = '/home/dong12/PMP_240131/pcmdi_metrics/pcmdi_metrics/monsoon_wang/output'

# Threshold
threshold = 2.5 / 86400
