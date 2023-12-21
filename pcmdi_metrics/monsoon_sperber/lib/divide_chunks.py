from __future__ import print_function

import sys

import numpy as np
import scipy.interpolate as interp
import time

""" For pentad,
Code taken from https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
"""
# Yield successive n-sized
# chunks from data.


def divide_chunks(data, n):
    # looping till length data
    #for i in range(0, len(data), n):
    for i in range(0, data.time.shape[0], n):

        yield data[i : i + n]


""" Above code advanced considering leap year
"""


def divide_chunks_advanced(data, n, debug=False):
    # Double check first date should be Jan 1 (except for SH monsoon)
#     tim = data.getTime()
#     calendar = tim.calendar
#     month = tim.asComponentTime()[0].month
#     day = tim.asComponentTime()[0].day

    timechk1 = time.time()
    print("AAAAAAAAA timeAAA line 36: ", time.time()-timechk1)
    tim = data.time.dt
    month = tim.month[0]
    day = tim.day[0]
    calendar = "gregorian"
    print("AAAAAAAAA timeAAA line 41: ", time.time()-timechk1)
    if debug:
        print("debug: first day of year is " + str(month) + "/" + str(day))
    if month not in [1, 7] or day != 1:
        sys.exit(
            "error: first day of year time series is " + str(month) + "/" + str(day)
        )
        
    # Check number of days in given year
    #nday = len(data)
    nday = data.time.shape[0]
    
    print('nday. =   ',nday)
    
    print("AAAAAAAAA timeAAA line 55: ", time.time()-timechk1)

    if nday in [365, 360]:
        # looping till length data
        for i in range(0, nday, n):
            yield data[i : i + n]
        print("AAAAAAAAA timeAAA line 61: ", time.time()-timechk1)
    elif nday == 366:
        # until leap year day detected
        for i in range(0, nday, n):
            # Check if leap year date included
            leap_detect = False
            for ii in range(i, i + n):
#                 date = data.getTime().asComponentTime()[ii]
#                 month = date.month
#                 day = date.day
                date = data.time.dt
                month = date.month[ii]
                day = date.day[ii]
                if month == 2 and day > 28:
                    if debug:
                        print("debug: leap year detected:", month, "/", day)
                    leap_detect = True
            print("AAAAAAAAA timeAAA line 78: ", time.time()-timechk1)
            if leap_detect:
                yield data[i : i + n + 1]
                tmp = i + n + 1
                break
            else:
                yield data[i : i + n]
                
        print("AAAAAAAAA timeAAA line 86: ", time.time()-timechk1)
        # after leap year day passed
        if leap_detect:
            for i in range(tmp, nday, n):
                yield data[i : i + n]
    elif nday == 361 and calendar == "360_day":
        # Speacial case handling for HadGEM2 family where time bounds was not
        # properly saved, so include next year's first day in time series
        if debug:
            print("debug: 361 to 360 revise: l.shape, before:", data.shape)
        data = data[0:360]
        if debug:
            print("debug: 361 to 360 revise: l.shape, after:", data.shape)
        # looping till length data
        for i in range(0, nday, n):
            yield data[i : i + n]
        print("AAAAAAAAA timeAAA line 102: ", time.time()-timechk1)
    else:
        sys.exit("error: number of days in year is " + str(nday))
        
    print('chunks_advanced return =  ', data)


def interp1d(data, ref_length, debug=False):
    data = np.array(data)
    data_interp = interp.interp1d(np.arange(data.size), data)
    data2 = data_interp(np.linspace(0, data.size - 1, ref_length))
    if debug:
        print("debug: 1d interpolation")
        print("debug: length before interp: ", len(data))
        print("debug: length after interp: ", len(data2))
    return data2
