from __future__ import print_function

import cdms2
import cdtime
import cdutil
import MV2
import numpy as np
import os
import pcmdi_metrics
import sys

from argparse import RawTextHelpFormatter
from genutil import StringConstructor

""" NOTE FOR ISSUES
1. syear/eyear given by parameter file need to be refered in the code
2. ocean mask for land only is not complete; refer placeholder
3. pathin need to be fully replaced by modpath
4. reference data (obs) is yet to be used
5. 72 pentad to 73 pentad interpolation need to be added for HadGEM2 models 
6. Adding of custom domain maybe needed to test Indian region as in Sperber & Annamalai 2014 Clim Dyn
   (or define the domain in the share/default_regions.py)
7. Make the results_dir aknowledge the tree structure
8. use unit adjust parameter in the code
"""
 
libfiles = ['argparse_functions.py',]

for lib in libfiles:
    exec(compile(open(os.path.join('../lib/', lib)).read(),
                 os.path.join('../lib/', lib), 'exec'))

# =================================================
# Hard coded options... will be moved out later
# -------------------------------------------------
pathin = '/work/cmip5-test/new/historical/atmos/day/pr/'
 
lst = os.listdir(pathin)

#list_monsoon_regions = ['ASM', 'NAMM']  # Will be added later
list_monsoon_regions = ['ASM']  # Will be added later

regions_specs = {}
exec(compile(open(sys.prefix + "/share/pmp/default_regions.py").read(),
             sys.prefix + "/share/pmp/default_regions.py", 'exec'))

# =================================================
# Some functions... will be moved out later
# -------------------------------------------------
""" For pentad,
Code taken from https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
"""
# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):
     
    # looping till length l
    for i in range(0, len(l), n): 
        yield l[i:i + n]
 
# How many elements each
# list should have
n = 5


def model_land_only(d):
    # masking out land should come here
    print('placeholder for mask out ocean')
    return d

# =================================================
# Collect user defined options
# -------------------------------------------------
P = pcmdi_metrics.driver.pmp_parser.PMPParser(
        description='Runs PCMDI Monsoon Sperber Computations',
        formatter_class=RawTextHelpFormatter)
P = AddParserArgument(P)
param = P.get_parameter()

# Pre-defined options
mip = param.mip
exp = param.exp
fq = param.frequency
realm = param.realm

# On/off switches
nc_out = param.nc_out  # Record NetCDF output
plot = param.plot # Generate plots

# Path to model data as string template
modpath = StringConstructor(param.modpath)
modpath_lf = StringConstructor(param.modpath_lf)

# Check given model option
models = param.modnames
print('models:', models)

# Realizations
realization = param.realization
print('realization: ', realization)

# Output
outdir = param.results_dir
print('outdir: ', outdir)

# Create output directory
if not os.path.exists(outdir):
    os.makedirs(outdir)

# Debug
debug = param.debug
print('debug: ', debug)

# Variables
var = param.varModel

# Year
syear = param.msyear
eyear = param.meyear
YearCheck(syear, eyear, P)

osyear = param.osyear
oeyear = param.oeyear
YearCheck(osyear, oeyear, P)

# =================================================
# Debugging tool
# -------------------------------------------------
# Open canvas for debug plot
if debug:
    import matplotlib.pyplot as plt
    import math
    ax = {}
    if len(list_monsoon_regions) > 1:
        nrows = math.ceil(len(list_monsoon_regions)/2.)
        ncols = 2
    else:
        nrows = 1
        ncols = 1

    fig = plt.figure()
'''
    for i, region in enumerate(list_monsoon_regions):
        ax[region] = plt.subplot(nrows, ncols, i+1)
        print('debug: region', region, 'nrows', nrows, 'ncols', ncols, 'index', i+1)
        ax[region].set_xlabel('pentad count')
        ax[region].set_ylabel('pentad precip mm/d')
        if ncols > 1 and (i+1)%2 == 0:
            ax[region].set_ylabel('')
        if nrows > 1 and math.ceil((i+1)/float(ncols)) < ncols:
            ax[region].set_xlabel('')
'''

# =================================================
# Loop start 
# -------------------------------------------------
for l in lst[0:1]:  # model loop
#for l in lst[0:2]:  # model loop

#for model in models:
#    print(' ----- ', model, ' ---------------------')

    mip = l.split('/')[-1].split('.')[0]
    model = l.split('/')[-1].split('.')[1]
    exp = l.split('/')[-1].split('.')[2]
    run = l.split('/')[-1].split('.')[3]

    #model_path_list = os.popen(
    #    'ls '+modpath(model=model, realization=realization,
    #    variable=var)).readlines() 

    #if debug:
    #    print('debug: model_path_list: ', model_path_list)
 
    print(pathin + l)
    fc = cdms2.open(pathin + l)
    d = fc['pr']  # NOTE: square brackets does not bring data into memory, only coordinates!
    t = d.getTime()
    c = t.asComponentTime()
   
    startYear = c[0].year
    endYear = c[-1].year

    startMonth = c[0].month
    endMonth = c[-1].month

    # Consider year only when entire calendar available
    if startMonth > 1:
        startYear += 1
    if endMonth < 12:
        endYear -= 1

    if debug:
        print('debug: startYear: ', type(startYear), startYear)
        print('debug: startMonth: ', type(startMonth), startMonth)
        print('debug: endYear: ', type(endYear), endYear)
        print('debug: endMonth: ', type(endMonth), endMonth)

    if debug:
        endYear = startYear + 1

    if nc_out:
        output_file_name = '_'.join([mip, model, exp, run])
        fout = cdms2.open(os.path.join(outdir, output_file_name+'.nc'), 'w')

    list_pentad_time_series = {}  # Archive individual year pentad time series for composite
    for region in list_monsoon_regions:
        list_pentad_time_series[region] = []

    if debug:
        for i, region in enumerate(list_monsoon_regions):
            ax[region] = plt.subplot(nrows, ncols, i+1)
            print('debug: region', region, 'nrows', nrows, 'ncols', ncols, 'index', i+1)
            ax[region].set_xlabel('pentad count')
            ax[region].set_ylabel('pentad precip mm/d')
            if ncols > 1 and (i+1)%2 == 0:
                ax[region].set_ylabel('')
            if nrows > 1 and math.ceil((i+1)/float(ncols)) < ncols:
                ax[region].set_xlabel('')
       
    for year in range(startYear, endYear+1):  # year loop, endYear+1 to include last year
        d = fc('pr',
               time=(cdtime.comptime(year),cdtime.comptime(year+1)),
               latitude=(-90,90))
        d = MV2.multiply(d, 86400.)  # unit change
        d = model_land_only(model, d, model_lf_path)
        print('debug: year: ', year)
        print('debug: d.shape: ', d.shape)
      
        for region in list_monsoon_regions:
            d_sub = d(regions_specs[region]['domain'])  # extract for monsoon region
            d_sub_aave = cdutil.averager(d_sub, axis='xy', weights='weighted')  # area average

            if debug: 
                print('debug: region: ', region)
                print('debug: d_sub.shape: ', d_sub.shape)
                print('debug: d_sub_aave.shape: ', d_sub_aave.shape)
  
            list_d_sub_aave_chunks = list(divide_chunks(d_sub_aave, n)) 
            pentad_time_series = []
            for d_sub_aave_chunk in list_d_sub_aave_chunks:
                if d_sub_aave_chunk.shape[0] == n:  # ignore when chunk length is shorter than defined
                    ave_chunk = cdutil.averager(d_sub_aave_chunk, axis='t')
                    pentad_time_series.append(float(ave_chunk))
            print('pentad_time_series', year, ': ', pentad_time_series)

            if debug:
                if year == startYear:
                    label = 'Individual year'
                else:
                    label = ''
                ax[region].plot(np.array(pentad_time_series), c='grey', label=label)

            if nc_out:
                fout.write(MV2.array(pentad_time_series), id=region+'_'+str(year))

            list_pentad_time_series[region].append(MV2.array(pentad_time_series))

    # Get composite for each region
    for region in list_monsoon_regions:
        composite_pentad_time_series = cdutil.averager(
            MV2.array(list_pentad_time_series[region]),
            axis=0,
            weights='unweighted')
        composite_pentad_time_series.setAxis(
            0, MV2.array(pentad_time_series).getAxis(0))
        if nc_out:
            fout.write(composite_pentad_time_series, id=region+'_comp')
        if debug:
            ax[region].plot(
                np.array(composite_pentad_time_series),
                c='red',
                label='Composite')
            ax[region].set_title(region)
            ax[region].legend(loc=4)

    if debug:
        fig.suptitle(
            'Precipitation pentad time series\n'
            +', '.join([mip, model, exp, run, str(startYear)+'-'+str(endYear)]))
        plt.subplots_adjust(top=0.85)
        plt.savefig(os.path.join(outdir, '_'.join([mip, model, exp, run])+'.png'))
        plt.clf()

    if nc_out:
        fout.close()
