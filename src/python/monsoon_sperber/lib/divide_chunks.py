from __future__ import print_function
import scipy.interpolate as interp
import sys

""" For pentad,
Code taken from https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
"""
# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i+n]

""" Above code advanced considering leap year
"""
def divide_chunks_advanced(l, n, debug=False):
    # Double check first date should be Jan 1 (except for SH monsoon)
    tim = l.getTime()
    calendar = tim.calendar
    month = tim.asComponentTime()[0].month
    day = tim.asComponentTime()[0].day
    if debug: print('debug: first day of year is '+str(month)+'/'+str(day))
    if month not in [1,7] or day != 1:
        sys.exit('error: first day of year time series is '+str(month)+'/'+str(day))

    # Check number of days in given year
    nday = len(l)

    if nday in [365, 360]:
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i+n]
    elif nday == 366:
        # until leap year day detected
        for i in range(0, len(l), n):
            # Check if leap year date included
            leap_detect = False
            for ii in range(i, i+n):
                date = l.getTime().asComponentTime()[ii]
                month = date.month
                day = date.day
                if month == 2 and day > 28:
                    if debug: 
                        print('debug: leap year detected:', month, '/', day)
                    leap_detect = True
            if leap_detect:
                yield l[i:i+n+1]
                tmp = i+n+1
                break
            else:
                yield l[i:i+n]
        # after leap year day passed
        if leap_detect:
            for i in range(tmp, len(l), n):
                yield l[i:i+n]
    elif nday == 361 and calendar == '360_day':
        # Speacial case handling for HadGEM2 family where time bounds was not 
        # properly saved, so include next year's first day in time series
        l = l[0:360]
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i+n]
    #elif nday == 360:
    #    l2 = interp1d(l, 365, debug=debug)
    #    # looping till length l
    #    for i in range(0, len(l2), n):
    #        yield l2[i:i+n]
    else:
        sys.exit('error: number of days in year is '+str(nday))


def interp1d(l, ref_length, debug=False):
    l = np.array(l)
    l_interp = interp.interp1d(np.arange(l.size), l)
    l2 = l_interp(np.linspace(0, l.size-1, ref_length))
    if debug:
        print('debug: 1d interpolation')
        print('debug: length before interp: ', len(l))
        print('debug: length after interp: ', len(l2))
    return l2
