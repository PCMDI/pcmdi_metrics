#!/usr/bin/env python
import argparse
import os
import sys
import glob
import tempfile
import subprocess
import shlex
import cdms2
import cdutil
try:
    import cmor
except:
    raise RuntimeError("Your UV-CDAT is not built with cmor")

parser = argparse.ArgumentParser(
    description='Generates Climatologies from files')

p = parser.add_argument_group('processing')
p.add_argument("-v", "--vars",
               nargs="*",
               dest="vars",
               default=None,
               required=True,
               help="variables to use for climatology")
p.add_argument("-t", "--threshold",
               dest='threshold',
               default=.5,
               type=float,
               help="Threshold bellow which a season is considered as " +
               "not having enough data to be computed")
p.add_argument("-c", "--climatological_season",
               dest="seasons",
               default=["all"],
               nargs="*",
               choices=["djf", "DJF", "ann", "ANN", "all", "ALL",
                        "mam", "MAM", "jja", "JJA", "son", "SON", "year",
                        "YEAR"],
               help="Which season you wish to produce"
               )
p.add_argument("-s", "--start",
               dest="start",
               default=None,
               help="Start for climatology: date, value or index " +
               "as determined by -i arg")
p.add_argument("-e", "--end",
               dest="end",
               default=None,
               help="End for climatology: date, value or index " +
               "as determined by -I arg")
p.add_argument("-i", "--indexation-type",
               dest="index",
               default="date",
               choices=["date", "value", "index"],
               help="indexation type")
p.add_argument("-f", "--files",
               dest="files",
               help="Input file",
               nargs="+")
p.add_argument("-b", "--bounds",
               action="store_true",
               dest="bounds",
               default=False,
               help="reset bounds to monthly")
c = parser.add_argument_group("CMOR options")
c.add_argument("-D", "--drs",
               action="store_true",
               dest="drs",
               default=False,
               help="Use drs for output path"
               )
c.add_argument("-T", "--tables",
               dest="tables",
               help="path where CMOR tables reside")
c.add_argument("-U", "--units",
               dest="units",
               nargs="*",
               help="variable(s) units, in same order " +
               "as -v argument")
c.add_argument("-V", "--cf-var",
               dest="cf_var",
               nargs="*",
               help="variable(s) name in CMOR tables, in same order " +
               "as -v argument")
c.add_argument("-E","--experiment_id",default=None,
        help="'experiment id' for this run (will try to get from input file",
        )
c.add_argument("-I","--institution",default=None,
        help="'institution' for this run (will try to get from input file",
        )
c.add_argument("-S","--source",default=None,
        help="'source' for this run (will try to get from input file",
        )

cmor_xtra_args = ["contact","references","model_id",
                "institute_id","forcing",
                "parent_experiment_id",
                "parent_experiment_rip",
                "realization","comment","history",
                "branch_time","physics_version",
                "initialization_method",
                ]
for x in cmor_xtra_args:
    c.add_argument("--%s" % x,default=None,
            dest = x,
            help="'%s' for this run (will try to get from input file" % x
            )

A = parser.parse_args(sys.argv[1:])
if len(A.files) == 0:
    raise RuntimeError("You need to provide at least one file for input")

if len(A.files) == 1:
    A.files = glob.glob(A.files[0])

for f in A.files:
    if not os.path.exists(f):
        raise RuntimeError("file '%s' doe not exits" % f)
if len(A.files) > 1:
    print "Multiple files sent, running cdscan on them"
    xml = tempfile.mkstemp(suffix=".xml")[1]
    P = subprocess.Popen(
        shlex.split(
            "cdscan -x %s %s" %
            (xml,
             " ".join(
                 A.files))))
    P.wait()
    A.files = xml
else:
    A.files = A.files[0]
    xml = None


# season dictionary
season_function = {
    "djf": cdutil.times.DJF,
    "mam": cdutil.times.MAM,
    "jja": cdutil.times.JJA,
    "son": cdutil.times.SON,
    "ann": cdutil.times.ANNUALCYCLE,
    "year": cdutil.times.YEAR,
}
filein = cdms2.open(A.files)
def checkCMORAttribute(att,source=filein):
    res = getattr(A,att)
    if res is None:
        if hasattr(source,att):
            res = getattr(source,att)
        else:
            raise RuntimeError("Could not figure out the CMOR '%s'" % att)
    return res

fvars = filein.variables.keys()
for ivar,v in enumerate(A.vars):
    if v not in fvars:
        raise RuntimeError(
            "Variable '%s' is not contained in input file(s)" %
            v)
    V = filein[v]
    tim = V.getTime().clone()
    # "monthly"
    if A.bounds:
        cdutil.times.setTimeBoundsMonthly(tim)
    # Now make sure we can get the requested period
    if A.start is None:
        i0 = 0
    else:  # Ok user specified a start time
        if A.index == "index":  # index-based slicing
            if int(A.start) >= len(tim):
                raise RuntimeError(
                    "For variable %s you requested start time to be at index: %i but the file only has %i time steps" %
                    (v, int(
                        A.start), len(tim)))
            i0 = int(A.start)
        elif A.index == "value":  # actual value used for slicing
            v0 = float(A.start)
            try:
                i0, tmp = tim.mapInterval((v0, v0, 'cob'))
            except:
                raise RuntimeError(
                    "Could not find value %s for start time for variable %s" %
                    (A.start, v))
        elif A.index == "date":
            v0 = A.start
            try:
                i0, tmp = tim.mapInterval((v0, v0, 'cob'))
            except:
                raise RuntimeError(
                    "Could not find start time %s for variable: %s" %
                    (A.start, v))

    if A.end is None:
        i1 = None
    else:  # Ok user specified a end time
        if A.index == "index":  # index-based slicing
            if int(A.end) >= len(tim):
                raise RuntimeError(
                    "For variable %s you requested end time to be at index: %i but the file only has %i time steps" %
                    (v, int(
                        A.end), len(tim)))
            i1 = int(A.end)
        elif A.index == "value":  # actual value used for slicing
            v0 = float(A.end)
            try:
                tmp, i1 = tim.mapInterval((v0, v0, 'cob'))
            except:
                raise RuntimeError(
                    "Could not find value %s for end time for variable %s" %
                    (A.end, v))
        elif A.index == "date":
            v0 = A.end
            try:
                tmp, i1 = tim.mapInterval((v0, v0, 'cob'))
            except:
                raise RuntimeError(
                    "Could not find end time %s for variable: %s" %
                    (A.end, v))
    # Read in data
    data = V(time=slice(i0, i1))
    print "DATA:", data.shape
    if A.bounds:
        cdutil.times.setTimeBoundsMonthly(data)
    # Now we can actually read and compute the climo
    seasons = [s.lower() for s in A.seasons]
    if "all" in seasons:
        seasons = ["djf", "mam", "jja", "son", "year", "ann"]

    for season in seasons:
        s = season_function[season].climatology(data)
        print season, s.shape
        inst = checkCMORAttribute("institution")
        src = checkCMORAttribute("source")
        exp = checkCMORAttribute("experiment_id")
        xtra={}
        for x in cmor_xtra_args:
            try:
                xtra[x] = checkCMORAttribute(x)
            except:
                pass
        cal = data.getTime().getCalendar()  # cmor understand cdms calendars
        error_flag = cmor.setup(
                               inpath='.', 
            netcdf_file_action=cmor.CMOR_REPLACE, 
            set_verbosity=cmor.CMOR_NORMAL, 
            exit_control=cmor.CMOR_NORMAL,
            logfile='logfile',
            create_subdirectories=int(A.drs))
        error_flag = cmor.dataset(
                experiment_id=exp,
                outpath='Test',
                institution=inst,
                source=src,
                calendar=cal,
                **xtra
                )
        table = cmor.load_table("pcmdi_metrics")

        # Ok CMOR is ready let's create axes
        cmor_axes = []
        for ax in s.getAxisList():
            if ax.isTime():
                table_entry = "time2"
                ntimes = len(ax)
            elif ax.isLatitude():
                table_entry = "latitude"
            elif ax.isLongitude():
                table_entry = "longitude"
            elif ax.isLevel():  # Need work here for sigma
                table_entry = "plevs"
            ax_id = cmor.axis(table_entry=table_entry,
                    units=ax.units, 
                    coord_vals=ax[:],
                    cell_bounds=ax.getBounds()
                    )
            print ax.id,ax_id
            cmor_axes.append(ax_id)
        # Now create the variable itself
        if A.cf_var is not None:
            var_entry = A.cf_var[ivar]
        else:
            var_entry = data.id

        units = A.units
        if units is None:
            units = data.units
        else:
            units = units[ivar]
        print "units:",units,var_entry
        var_id = cmor.variable(table_entry = var_entry,
                units = units,
                axis_ids = cmor_axes,
                type = s.typecode(),
                missing_value = s.missing_value)

        print "writing data?"
        # And finally write the data
        data2 = s.filled(s.missing_value)
        print data2.shape
        cmor.write(var_id,data2,ntimes_passed=ntimes)
        print "Done writing"

        # Close cmor
        path = cmor.close(var_id,file_name = True)
        print "Saved to:",path

        cmor.close()
        print "closed cmor"


# clean up
if xml is not None:
    os.remove(xml)
