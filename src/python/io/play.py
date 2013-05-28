#!/usr/local/uvcdat/bin/python

# At the moment, this file is scratch space for playing with how to make a plot.
# It will turn into something real.

import cdms2, math
from filetable import *

# When we come in here, we should have a filetable, and we should know the standard_names of the
# variables we want to plot, and their time and space ranges.  Then
#  filetable.find_file( varname )  (ranges are optional arguments)
# can be called once or twice to get one or two file lists, one for each variable.
# And actually, find_file returns a rowlist which has more useful information (the file is row.fileid).

# TO DO: look at plotting functions.  What input?  How will I concatenate data, dealing
# with out-of-bounds and missing data events?

# Here's how I would normally plot a variable interactively, values in vertical axis,
# nothing (except the array index) in the horizontal axis:
# f=cdms2.open(file)
# v=vcs.init()
# tlt=f['eqmsu_tlt']
# len0 = tlt.shape[0]
# v.plot(tlt[0:len0:12,0,0])

# For starters, just do such a simple plot and for one file.
# Later we'll have to merge data from multiple files.  Merging requires a common axis
# to determine the ordering, the array index won't work any more.
file0 = filelist[0]
f=cdms2.open(file0)
v=vcs.init()  # don't do this more than once!
# Here convert from a standard_name to the actual variable name, var; as in the method interesting_variables.
fvar=f[var]
len0 = fvar.shape[0]
v.plot(fvar[0:len0])  # if fvar is >=2D, need to detect that and freeze the other indices
# Let's hope that vcs plot has an option to write to a png or jpg file too.
f.close()

# Now let's merge files/rows.  In this case there has to be a common axis variable, say time.
# For this messing around I won't check that the time axes exist and have the same units.
# (Actually, time units are different in many cases, e.g. GISS adjusts time units so each file's
# time starts at 0.)
# I also, for now, will assume without checking that time axes do not overlap.
rows.sort( key=(lambda r: r.timerange.lo) )
# Here convert from a standard_name to the actual variable name, var; as in method interesting_variables.
plotvar = []
plottime = []
for fil in filelist:
    f=cdms2.open(fil)
    fvar=f[var]
    time = fil.axes['time']
    plotvar += fvar[:]
    plottime += time[:]
v.plot( plottime, plotvar )  # if the syntax be v.plot(x,y); I'm waiting for a working cdat to try

# But actually all plots and tables are based on an average over years, with month or season
# held fixed.

# Even without graphics, I can do the tables, e.g.
    # DIAG SET 1: DJF MEANS GLOBAL

    # TEST CASE: cam3_5_fv1.9x2.5 (yrs 1979-2005)

    # CONTROL CASE: OBS data

    # Variable     cam3_5_fv1.9x2.5        OBS data        cam3_5_fv1.9x2.5        RMSE
    #                                                      -OBS data
    # RESTOM             8.213            -999.000          -999.000      -999.000
    # RESSURF            7.605            -999.000          -999.000      -999.000
    # RESTOA_CERES-EBAF  9.937               7.699             2.238        13.767
    # RESTOA_ERBE        9.937               7.330             2.607        13.609
    # SOLIN_CERES-EBAF 351.923             350.113             1.811         2.417
# Probably RMSE = Root Mean Square Error.

# So let's assume that all data is monthly averages, and average over years, over
# a zone, etc.
# Doing this kind of calculation depends on the file's data structure - CF-compliant
# will be different from CESM, to name two which we plan to support.  That calls for
# a class:
class basic_file_conventions:
    # abstract class, normally one will construct one of its children
    def time_averages( filepath, varname ): return {}
    def zonal_mean( filepath, varvals, latmin, latmax ): return None
    #etc
# For now I'll just define functions, to work with typical CF-compliant files, because 
# I'm not sure that I'll get the class structure right without doing some plots first.

# One file, first.  This function/method assumes that the variable fvar, obtainable as f['varname'],
# has time as its first dimension, the variable's contents are monthly means, that it has time as a
# cdms2 axis, and that the time interval is a month without gaps.
# This function would naturally be a method of CF_filefmt:
def time_averages( filepath, varname ):
    """Computes and returns averages of variable varname over:
    each month, summer (June-July-August), winter (December-January-February), and the whole year.
    """
    f=cdms2.open(filepath)
    var=f[varname]     # var obtained by conversion from a standard_name
    time = f.axes['time']
    # The monthly assumption means we don't have to worry about calendars
    # And, for now, don't worry about missing data.
    # >> There has to be a cleaner way to initialize these:
    monvar = [0,0,0,0,0,0,0,0,0,0,0,0]*var[0]
    annvar = 0*var[0]
    # Note that monvar,annvar,etc are still multidimensional arrays; we're just taking out time.
    for im in range(12):
        for it in range( 0, len(time), 12 ):
            if im+it<len(time):
                monvar[im] += var[im+it]
        monvar[im] /= math.floor( len(time) / 12. )
    annvar += monvar[im]
    annvar /= 12.
    jjavar = (monvar[5]+monvar[6]+monvar[7])/3
    djfvar = (monvar[11]+monvar[0]+monvar[1])/3
    f.close()
    return { 'mons':monvar, 'jja':jjavar, 'djf':djfvar, 'ann':annvar }

# AMWG has plots and tables of many variables which I do not recognize.  They may be
# "derived data" which we would get by simple computations.  But for now, I'll use existing variables.

# AMWG often displays means - global, or zonal, e.g. tropics: -20 to 20 degrees latitude.
# So here's a sample function to compute them, for CF-compliant files.
# I'm going to assume var[time,lat,lon] .  More complicated cases
# exist, e.g. with levels or especially involving the coordinates attribute.  I'm not sure
# whether the lat,lon order is standardized in CF or just common.  Anyway, this should be made
# to work with non-CF too!  This is just a start:
def zonal_mean( fil, varvals, latmin, latmax ):
    """returns the mean of the variable over the supplied latitude range
    fil is one of the time-split files used to obtain the variable.
    varvals is a list or array of the variable values"""
    # Important: I don't know what weighting function to use, but there should be one!!!
    zm = 0
    lat = fil.axes['lat']
    lon = fil.axes['lon']
    for i in range(len(lat)):
        for j in range(len(lon)):
            if latmin<=lat[i] and lat[i]<latmax:
                zm += varvals[i,j]
    # ... Boy, could this be coded better! 
    return zm

# At the high level, we will start with a file specification (e.g. top-level directory and "CMIP5")
# and output specifications.  Normally the user will provide just the file specification and we will
# have standard output specifications and run them all.
#
# An output specification will be the object which specifies, and probably initiates, output.
#  Logically it's defined by
# - data sources (filetables, computed from file specifications)
# - variables and their domains (as in a row object, but without the file)(1-2 at present)
# - reduction functions (e.g. zonal mean of a variable)
# - output type (e.g. table, line plot, contour plot)
# - axes (normally 2 or fewer after reductions)
# - presentation details (e.g. which axis is horizontal, title of graph, etc.)
# This calls for several class hierarchies.
# - the reduction function would be a method of a file format class, i.e. a child of basic_filefmt.
# - the output type - children of basic_outputter below
# - variable information - output_variable class below

class reduced_variable(row):
    """Specifies a 'reduced variable', which is a single-valued part of an output specification.
    This would be a variable(s) and its domain, a reduction function, and
    an axis or two describing the domain after applying the reduction function.
    Output may be based on one or two of these objects"""
    >>>> TO DO <<<<<
>>>> besides row information, this will have the reduction function;
>>>> and it will have a filetable in place of the file in a row object
>>>> Moreover, this will explicitly have one or two axes

class basic_outputter:
    """specifies output - e.g. a graph.  This is an abstract class."""
    def __init__( rv1, rv2=None, title="Basic Graph" ):
        _reduced_variable_1 = rv1
        _reduced_variable_2 = rv2
        _title=title
    def output():
        pass

class output_variable(row):
    """Specifies a variable used (perhaps indirectly) for output - variable name and domain.
    At the moment this is the same as filetable.row, except that we don't care about the file
    (which can be None).  But in the future they can be expected to diverge and maybe have a
    common ancestor."""



# TO DO:
# Given an output_variable, we have to identify the right files, open them and get
# the data we need, construct a transient variable or other suitable cdms2 variable,
# which may have missing data, then transform it with something like zonal_mean.
# The resulting cdms2 variable will be suitable for constructing a basic_outputter object and
# plotting.


# The following class structure is for handling plotting/output.  It feels wrong to
# me, and I may completely replace it after I get more experience, e.g. expanding it to do
# 2-3 types of plots with labels etc.

class line_plot(basic_outputter):
    def __init__( vcsv, rv1, rv2=None ):
        """The first argument is the return value of vcs.init().
        The second and third arguments are cdms2 variables."""
        basic_outputter.__init__( rv1, rv2 )
        # to do: add other initializations as needed; e.g. to specify the axes and axis titles.
        # Eventually the vcsv argument will be generalized to an output target, and typically,
        # should default to a png file.
        self._vcsv = vcsv
    def output():
        """writes out the actual line plot"""
        if len(rv1.shape)!=:
            raise Exception("line_plot sees wrong shape in rv1")
        if len(rv2.shape)!=0:
            raise Exception("line_plot sees wrong shape in rv2")
        _vcsv.plot( rv1[:], rv2[:] )

