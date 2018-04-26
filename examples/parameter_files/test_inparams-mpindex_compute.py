# SAMPLE PARAMETER FILE TO RUN PMP's WANG_MONSOON METRICS
# TESTED with data at PCMDI
# PJG Apr 26 2018

# EXECUTION
# >  mpindex_compute.py -p test_inparams-mpindex_compute.py

modpath = "/work/gleckler1/processed_data/cmip5clims_metrics_package-historical/pr_MODS_Amon_historical_r1i1p1_198101-200512-clim.nc"
reference_data_path = "/work/gleckler1/processed_data/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc"

modnames = ['GISS-E2-H-CC', 'CSIRO-Mk3-6-0']

outpathjsons = "./test_monsoon_metrics/"
jsonname = 'wang_monsoon_CMIP5_historical'

results_dir = './test_monsoon_diagnostics/'

