# EXAMPLE PARAMETER FILE TO RUN PMP's COVEY_DIURNAL CYCLE METRICS
# TESTED with data at PCMDI
# PJG 10/24/2018

#NEEDED: Command-line option failing 
#        Data used in this example needs to be accessible to external users 

# EXECUTION WITH (THIS) INPUT PARAMETER FILE:
# > compositeDiurnalStatisticsWrapped.py -p test_inparams_compositeDiurnalStatistics.py

# ALTERNATE EXECUTION VIA COMMAND LINE:
#compositeDiurnalStatisticsWrapped.py --modpath /work/durack1/cmip5/historical/atm/3hr/pr/ -t cmip5.%(model).historical.r1i1p1.3hr.atm.3hr.pr.%(version).latestX.xml --num_workers --model GFDL-ESM2M -f 1989 -l 1999 --results_dir ./example_diurnal_results

modpath = '/work/durack1/cmip5/historical/atm/3hr/pr/'
filename_template = "cmip5.%(model).historical.r1i1p1.3hr.atm.3hr.pr.%(version).latestX.xml"
num_workers = 3
model = 'GFDL-ESM2M'   #'*'   #'IPSL-CM5A-LR'
firstyear = 1989
lastyear = 1999 
results_dir = './example_diurnal_results'
