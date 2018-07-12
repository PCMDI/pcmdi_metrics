from __future__ import print_function

import cdms2
import cdtime
import cdutil
import MV2
import numpy as np
import os
import sys
 
pathin = '/work/cmip5-test/new/historical/atmos/day/pr/'
 
lst = os.listdir(pathin)

list_monsoon_regions = ['ASM', 'NAMM']  # Will be added later
#list_monsoon_regions = ['ASM']  # Will be added later

debug = True
nc_out = True

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
regions_specs = {}
exec(compile(open(sys.prefix + "/share/pmp/default_regions.py").read(),
             sys.prefix + "/share/pmp/default_regions.py", 'exec'))

'''For pentad,
taken from https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
'''
# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):
     
    # looping till length l
    for i in range(0, len(l), n): 
        yield l[i:i + n]
 
# How many elements each
# list should have
n = 5


def maskoutOcean(d):
    # masking out land should come here
    print('placeholder for mask out ocean')
    return d

#for l in lst[0:1]:  # model loop
for l in lst[0:2]:  # model loop

    project = l.split('/')[-1].split('.')[0]
    model = l.split('/')[-1].split('.')[1]
    exp = l.split('/')[-1].split('.')[2]
    run = l.split('/')[-1].split('.')[3]
 
    print(pathin + l)
    fc = cdms2.open(pathin + l)
    d = fc['pr']  # NOTE: square brackets does not bring data into memory, only coordinates!
    t = d.getTime()
    c = t.asComponentTime()
   
    startYear = c[0].year
    startMonth = c[0].month
    endYear = c[-1].year
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
        output_file_name = '_'.join([project, model, exp, run])
        fout = cdms2.open(output_file_name+'.nc', 'w')

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
        d = fc('pr',time=(cdtime.comptime(year),cdtime.comptime(year+1)))
        d = MV2.multiply(d, 86400.)  # unit change
        d = maskoutOcean(d)
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
            +', '.join([project, model, exp, run, str(startYear)+'-'+str(endYear)]))
        plt.subplots_adjust(top=0.85)
        plt.savefig('_'.join([project, model, exp, run])+'.png')
        plt.clf()

    if nc_out:
        fout.close()
