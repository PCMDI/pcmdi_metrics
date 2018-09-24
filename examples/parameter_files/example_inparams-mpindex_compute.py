# EXAMPLE INPUT PARAMETER FILE TO RUN PMP's WANG_MONSOON METRICS
# TESTED with data at PCMDI
# PJG 10/24/2018

#NEEDED: Data used in this example needs to be accessible to external users 

# EXECUTION WITH (THIS) INPUT PARAMETER FILE:
# >  mpindex_compute.py -p test_inparams-mpindex_compute.py

# ALTERNATE EXECUTION VIA COMMAND LINE:
# > mpindex_compute.py --modpath /work/gleckler1/processed_data/cmip5clims_metrics_package-historical/pr_MODS_Amon_historical_r1i1p1_198101-200512-clim.nc --reference_data_path /work/gleckler1/processed_data/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc --modnames "['GISS-E2-H-CC']" --outpj ./example_monsoon-wang_metrics/ --outnj monsoon-wang_CMIP5_historical --results_dir ./example_monsoon-wang_diagnostics/

modpath = "/work/gleckler1/processed_data/cmip5clims_metrics_package-historical/pr_MODS_Amon_historical_r1i1p1_198101-200512-clim.nc"
reference_data_path = "/work/gleckler1/processed_data/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc"
modnames = ['GISS-E2-H-CC', 'CSIRO-Mk3-6-0']
outpathjsons = "./example_monsoon-wang_metrics/"
jsonname = 'monsoon-wang_CMIP5_historical'
results_dir = './example_monsoon-wang_diagnostics/'

