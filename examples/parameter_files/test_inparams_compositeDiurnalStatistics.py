# SAMPLE PARAMETER FILE TO RUN PMP's COVEY_DIURNAL CYCLE METRICS
# TESTED with data at PCMDI
# PJG Apr 27 2018

# EXECUTION
# > compositeDiurnalStatisticsWrapped.py -p test_inparams_compositeDiurnalStatistics.py

modpath = '/work/durack1/cmip5/historical/atm/3hr/pr/'
filename_template = "cmip5.%(model).historical.r1i1p1.3hr.atm.3hr.pr.%(version).latestX.xml"
num_workers = 3
model = 'GFDL-ESM2M'   #'*'   #'IPSL-CM5A-LR'
firstyear = 1989
lastyear = 1999 
results_dir = './test_diurnal_results'
