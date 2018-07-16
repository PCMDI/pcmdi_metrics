""" For pentad,
Code taken from https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
"""
# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i+n]


def divide_chunks_advanced(l, n, debug=False):
    # Double check first date should be Jan 1 (except for SH monsoon)
    month = l.getTime().asComponentTime()[0].month
    day = l.getTime().asComponentTime()[0].day
    if debug: print('debug: first day of year is '+str(month)+'/'+str(day))
    if month != 1 or day != 1:
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
            for i in range(i, i+n):
                month = l.getTime().asComponentTime()[i].month
                day = l.getTime().asComponentTime()[i].day
                if month == 2 and day > 28:
                    if debug: print('debug: leap year detected')
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
    else:
        sys.exit('error: number of days in year is '+str(nday))
