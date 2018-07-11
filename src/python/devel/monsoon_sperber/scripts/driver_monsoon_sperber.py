from __future__ import print_function

import cdms2
import cdtime
import os
 
pathin = '/work/cmip5-test/new/historical/atmos/day/pr/'
 
lst = os.listdir(pathin)

list_regions = ['ASM']  # Will be added later
 
for l in lst[0:1]:  # model loop
 
    print(pathin + l)
    fc = cdms2.open(pathin + l)
    d = fc['pr']  # NOTE: square brackets does not bring data into memory, only coordinates!
    t = d.getTime()
    c = t.asComponentTime()
   
    startyear = c[0].year
    endyear = c[-1].year
    print(type(startyear), startyear)
    print(type(endyear), endyear)
   
    d = fc('pr',time=(cdtime.comptime(startyear),cdtime.comptime(startyear+1)))
    print(d.shape)
  
    for region in list_regions:
        print(region)
  
  
   
