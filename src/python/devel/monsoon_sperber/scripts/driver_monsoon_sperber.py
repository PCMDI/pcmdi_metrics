from __future__ import print_function

import cdms2
import cdtime
<<<<<<< HEAD
import cdutil
import MV2
import os
import sys
=======
import os
>>>>>>> fa6dbe72b84d02c34dace4e8c831410128b5a6ec
 
pathin = '/work/cmip5-test/new/historical/atmos/day/pr/'
 
lst = os.listdir(pathin)

list_regions = ['ASM']  # Will be added later
<<<<<<< HEAD

debug = True


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


=======
 
>>>>>>> fa6dbe72b84d02c34dace4e8c831410128b5a6ec
for l in lst[0:1]:  # model loop
 
    print(pathin + l)
    fc = cdms2.open(pathin + l)
    d = fc['pr']  # NOTE: square brackets does not bring data into memory, only coordinates!
    t = d.getTime()
    c = t.asComponentTime()
   
<<<<<<< HEAD
    startYear = c[0].year
    startMonth = c[0].month
    endYear = c[-1].year
    endMonth = c[-1].month

    # Consider entire calendar years only
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
        endYear = startYear
   
    for year in range(startYear, endYear+1):  # year loop, endYear+1 to include last year
        d = fc('pr',time=(cdtime.comptime(year),cdtime.comptime(year+1)))
        d = MV2.multiply(d, 86400.)  # unit change
        print('debug: year: ', year)
        print('debug: d.shape: ', d.shape)
      
        for region in list_regions:
            d_sub = d(regions_specs[region]['domain'])  # extract for monsoon region
            d_sub_aave = cdutil.averager(d_sub, axis='xy', weights='weighted')  # area average
            if debug: 
                print('debug: region: ', region)
                print('debug: d_sub.shape: ', d_sub.shape)
                print('debug: d_sub_aave.shape: ', d_sub_aave.shape)
  
            my_list = d_sub_aave
            list_d_sub_aave_chunks = list(divide_chunks(d_sub_aave, n)) 

            pentad_time_series = []
            for d_sub_aave_chunk in list_d_sub_aave_chunks:
                if d_sub_aave_chunk.shape[0] == n:  # ignore when chunk length is shorter than defined
                    ave_chunk = cdutil.averager(d_sub_aave_chunk, axis='t')
                    pentad_time_series.append(float(ave_chunk))
            print('pentad_time_series', year, ': ', pentad_time_series)

=======
    startyear = c[0].year
    endyear = c[-1].year
    print(type(startyear), startyear)
    print(type(endyear), endyear)
   
    d = fc('pr',time=(cdtime.comptime(startyear),cdtime.comptime(startyear+1)))
    print(d.shape)
  
    for region in list_regions:
        print(region)
  
  
   
>>>>>>> fa6dbe72b84d02c34dace4e8c831410128b5a6ec
