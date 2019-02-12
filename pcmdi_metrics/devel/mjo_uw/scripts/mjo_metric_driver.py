"""
Code written by Jiwoo Lee, LLNL. Feb. 2019
Inspired by Daehyun Kim and Min-Seop Ahn's MJO metrics.

Reference:
Ahn, MS., Kim, D., Sperber, K.R. et al. Clim Dyn (2017) 49: 4023.
https://doi.org/10.1007/s00382-017-3558-4 
"""
from __future__ import print_function
import cdms2
import cdtime
import cdutil
import datetime
import MV2
import numpy as np
import os
import sys

libfiles = ['lib_mjo.py',
            'debug_chk_plot.py']

for lib in libfiles:
    exec(compile(open(os.path.join('../lib/', lib)).read(),
                 os.path.join('../lib/', lib), 'exec'))

#===============================================================================
# User given options: debug, inputfile (GPCP daily)
#-------------------------------------------------------------------------------
debug = False 
plot = False 
#cmmGrid = True
cmmGrid = False
#UnitsAdjust = (True, 'multiply', 86400., 'mm d-1')
UnitsAdjust = (False, 0, 0, 0)
degX = 2.5  # grid distance for common grid (in degree)

#inputfile = '/p/user_pub/pmp/pmp_obs/orig/data/GPCP_v1.3_da/pr_GPCP-1DD_L3_v1.3_19961001-20161231.nc'
#var = 'pr'
inputfile = '/work/lee1043/cdat/pmp/MJO_metrics/UW_raw_201812/DATA/GPCPv1.2/daily.19970101_20101231.nc'
var = 'p'
startYear = 1997
endYear = 2010
segmentLength = 180  # number of time step for each segment (in day, in this case), need to keep this number as even number?

case_id = "{:v%Y%m%d-%H%M}".format(datetime.datetime.now())
result_dir = '../result/' + case_id
ncfileName = 'GPCP_stps_'+str(startYear)+'-'+str(endYear) # output netCDF file
if cmmGrid:
    ncfileName += '_cmmGrid'
#-------------------------------------------------------------------------------

# Open file to read daily dataset
if debug: print('debug: open file')
f = cdms2.open(inputfile)
d = f[var]
tim = d.getTime()
comTim = tim.asComponentTime()
calendar = tim.calendar

# Get starting and ending year and month
if debug: print('debug: check time')
first_time = comTim[0]
last_time = comTim[-1]

# Adjust years to consider only when continous NDJFMA is available
if first_time > cdtime.comptime(startYear, 11, 1):
    startYear += 1
if last_time < cdtime.comptime(endYear, 4, 30):
    endYear -= 1

# Number of grids for 2d fft input
NL = len(d.getLongitude())  # number of grid in x-axis (longitude)
if cmmGrid:
    NL = int(360/degX)
NT = segmentLength  # number of time step for each segment (need to be an even number)

if debug: endYear = startYear+2
if debug: print('debug: startYear, endYear:', startYear, endYear)
if debug: print('debug: NL, NT:', NL, NT) 

#
# Get daily climatology on each grid, then remove it to get anomaly
#
numYear = endYear - startYear
mon = 11
day = 1
# Store each year's segment in a dictionary: segment[year]
segment = {}
segment_ano = {}
daSeaCyc = MV2.zeros((NT, d.shape[1], d.shape[2]), MV2.float)
for year in range(startYear, endYear):
    print(year)
    segment[year] = subSliceSegment(d, year, mon, day, NT)
    # units conversion
    segment[year] = unit_conversion(segment[year], UnitsAdjust)
    # Get climatology of daily seasonal cycle
    daSeaCyc = MV2.add(
        MV2.divide(segment[year],float(numYear)),
        daSeaCyc)
# Remove daily seasonal cycle from each segment
if numYear > 1:
    for year in range(startYear, endYear):
        segment_ano[year] = Remove_dailySeasonalCycle(segment[year], daSeaCyc)

#
# Space-time power spectra
#
"""
Handle each segment (i.e. each year) separately.
1. Get daily time series (3D: time and spatial 2D)
2. Meridionally average (2D: time and spatial, i.e., longitude) 
3. Get anomaly by removing time mean of the segment
4. Proceed 2-D FFT to get power.
Then get multi-year averaged power after the year loop.
"""
# Define array for archiving power from each year segment
Power = np.zeros((numYear, NT + 1, NL + 1), np.float)

# Year loop for space-time spectrum calculation
if debug: print('debug: year loop start')
for n, year in enumerate(range(startYear, endYear)):
    print('chk: year:', year)
    d_seg = segment_ano[year]
    # Regrid: interpolation to common grid
    if cmmGrid:
        d_seg = interp2commonGrid(d_seg, degX, debug=debug)
    # Subregion, meridional average, and remove segment time mean
    d_seg_x_ano = get_daily_ano_segment(d_seg)
    # Compute space-time spectrum
    if debug: print('debug: compute space-time spectrum')
    Power[n, :, :] = space_time_spectrum(d_seg_x_ano)  

# Multi-year averaged power
Power = np.average(Power, axis=0)
# Generates axes for the decoration
Power, ff, ss = generate_axes_and_decorate(Power, NT, NL)
# Output for wavenumber-frequency power spectra
OEE = output_power_spectra(Power, ff, ss)
# NetCDF output
if not os.path.exists(result_dir):
    os.makedirs(result_dir)
ncfilePathName = os.path.join(result_dir, ncfileName)
write_netcdf_output(OEE, ncfilePathName)

# E/W ratio
ewr, eastPower, westPower = calculate_ewr(OEE)
print('ewr: ', ewr)
print('east power: ', eastPower) 
print('west power: ', westPower)

# Output to JSON

# Debug checking plot
if debug and plot:
    debug_chk_plot()
