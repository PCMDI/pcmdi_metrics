##########################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
##########################################################################

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'amip5_test'
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
# AMIP5 MODELS
test_data_set = [
    'CNRM-CM5',
    'CanAM4',
    'ACCESS1-3',
    'MRI-CGCM3',
    'bcc-csm1-1',
    'FGOALS-s2',
    'CCSM4',
    'NorESM1-M',
    'inmcm4',
    'IPSL-CM5A-MR',
    'CESM1-CAM5',
    'bcc-csm1-1-m',
    'FGOALS-g2',
    'IPSL-CM5A-LR',
    'GFDL-HIRAM-C180',
    'HadGEM2-A',
    'CMCC-CM',
    'GISS-E2-R',
    'GFDL-HIRAM-C360',
    'MPI-ESM-LR',
    'MIROC5',
    'GFDL-CM3',
    'IPSL-CM5B-LR',
    'MPI-ESM-MR',
    'MRI-AGCM3-2S',
    'MRI-AGCM3-2H',
    'ACCESS1-0',
    'BNU-ESM',
    'CSIRO-Mk3-6-0',
    'EC-EARTH']

# VARIABLES AND OBSERVATIONS TO USE
vars = [
    'ta_850',
    'ta_200',
    'ua_850',
    'ua_200',
    'va_850',
    'va_200',
    'zg_500',
    'rlut',
    'rsut',
    'rlutcs',
    'rsutcs',
    'tas']

# Observations to use at the moment "default" or "alternate"
reference_data_set = 'all'
# ref = ['default']  #,'alternate','ref3']
ext = '.xml'  # '.nc'
ext = '.nc'

# INTERPOLATION OPTIONS
target_grid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'esmf'  # 'regrid2' # OPTIONS: 'regrid2','esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
regrid_tool_ocn = 'esmf'    # OPTIONS: "regrid2","esmf"
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'

# SIMULATION PARAMETERS
period = '1980-2005'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_test_clims = True  # True or False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

# Templates for climatology files
# TEMPLATE EXAMPLE:
# cmip5.GFDL-ESM2G.historical.r1i1p1.mo.atm.Amon.rlut.ver-1.1980-1999.AC.nc
filename_template = "%(variable)_%(model_version)_Amon_amip_r1i1p1_198001-200512-clim.nc"

# ROOT PATH FOR MODELS CLIMATOLOGIES
test_data_path = '/work/gleckler1/processed_data/cmip5clims_metrics_package-amip/'
# ROOT PATH FOR OBSERVATIONS
reference_data_path = '/work/gleckler1/processed_data/metrics_package/obs/'
# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = '/work/gleckler1/processed_data/metrics_package/metrics_results/" +\
        "cmip5clims_metrics_package-amip'
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
test_clims_interpolated_output = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims-amip/'
# FILENAME FOR INTERPOLATED CLIMATOLGIES OUTPUT
filename_output_template = "cmip5.%(model_version).amip.r1i1p1.mo.%(table_realm)." +\
    "%(variable)%(level).ver-1.%(period).interpolated.%(regridMethod).%(targetGridName).AC%(ext)"
