#!/usr/bin/env python
from __future__ import print_function
import os
import tempfile
import cdms2
import cdutil
import numpy
import cdtime
from pcmdi_metrics.driver.pmp_parser import PMPParser
import glob
import genutil
import cdp

try:
    import cmor
    hasCMOR = True
except Exception:
    hasCMOR = False

parser = PMPParser(description='Generates Climatologies from files')

def load_parser(parser):
    p = parser.add_argument_group('processing')
    p.add_argument(
        "--verbose",
        action="store_true",
        dest="verbose",
        help="verbose output",
        default=True)
    p.add_argument(
        "--quiet",
        action="store_false",
        dest="verbose",
        help="quiet output")
    p.add_argument("-v", "--variable",
                dest="variable",
                default=None,
                # required=True,
                help="variable to use for climatology")
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
    p.add_argument("-o", "--output_filename_template",
                help="template for output filename",
                default="%(variable)_PMP_%(model_id)_%(experiment_id)_" +
                "r%(realization)i%(initialization_method)p%(physics_version)" +
                "_%(start)-%(end)-clim-%(season).nc"
                )
    p.add_argument("-f", "--filename_template",
                dest="filename_template",
                help="Input file template")
    p.add_argument("-m", "--model",
                dest="model",
                help="Model Name")
    p.add_argument("-b", "--bounds",
                action="store_true",
                dest="bounds",
                default=False,
                help="reset bounds to monthly")
    p.add_argument("--mapping_dictionary", default={}, type=dict, help="A mapping dictionary to map undefnied parameters")
    # parser.use("results_dir", p)
    parser.use("results_dir")
    parser.use("modpath")
    c = parser.add_argument_group("CMOR options")
    c.add_argument("--use-cmor", dest="cmor", default=False, action="store_true")
    c.add_argument("-D", "--drs",
                action="store_true",
                dest="drs",
                default=False,
                help="Use drs for output path"
                )
    c.add_argument("-T", "--table",
                dest="table",
                nargs="+",
                help="CMOR table")
    c.add_argument("-U", "--units",
                dest="units",
                help="variable(s) units")
    c.add_argument("-V", "--cf-var",
                dest="cf_var",
                help="variable name in CMOR tables")
    c.add_argument("-E", "--experiment_id", default=None,
                help="'experiment id' for this run (will try to get from input file",
                )
    c.add_argument("-I", "--institution", default=None,
                help="'institution' for this run (will try to get from input file",
                )
    c.add_argument("-S", "--source", default=None,
                help="'source' for this run (will try to get from input file",
                )
    c.add_argument("-X", "--variable_extra_args", default="{}",
                help="Potential extra args to pass to cmor_variable call",
                )

    cmor_xtra_args = ["contact", "references", "model_id",
                    "institute_id", "forcing",
                    "parent_experiment_id",
                    "parent_experiment_rip",
                    "realization", "comment", "history",
                    "branch_time", "physics_version",
                    "initialization_method",
                    ]
    for x in cmor_xtra_args:
        c.add_argument("--%s" % x, default=None,
                    dest=x,
                    help="'%s' for this run (will try to get from input file" % x
                    )


load_parser(parser)

As = parser.get_parameters()

parser = PMPParser(description='Generates Climatologies from files')
load_parser(parser)

for A in As:
    for tmpl in [A.modpath, A.filename_template, A.output_filename_template]:
        con = genutil.StringConstructor(tmpl)
        print("TEMPLE:", con.template)
        for k in con.keys():
            print("ADDING OPTION:",k)
            parser.add_argument("--{}".format(k))

def getCalendarName(cal):
    for att in dir(cdtime):
        if getattr(cdtime, att) == cal:
            return att[:-8].lower()


def dump_cmor(A, s, time, bounds):
    inst = checkCMORAttribute("institution")
    src = checkCMORAttribute("source")
    exp = checkCMORAttribute("experiment_id")
    xtra = {}
    for x in cmor_xtra_args:
        try:
            xtra[x] = checkCMORAttribute(x)
        except Exception:
            pass
    cal = data.getTime().getCalendar()  # cmor understand cdms calendars
    cal_name = getCalendarName(cal)
    if A.verbose:
        cmor_verbose = cmor.CMOR_NORMAL
    else:
        cmor_verbose = cmor.CMOR_QUIET
    tables_dir = os.path.dirname(A.table)
    cmor.setup(
        inpath=tables_dir,
        netcdf_file_action=cmor.CMOR_REPLACE,
        set_verbosity=cmor_verbose,
        exit_control=cmor.CMOR_NORMAL,
        #            logfile='logfile',
        create_subdirectories=int(A.drs))

    tmp = tempfile.NamedTemporaryFile(mode="w")
    tmp.write("""{{
           "_control_vocabulary_file": "CMIP6_CV.json",
           "_AXIS_ENTRY_FILE":         "CMIP6_coordinate.json",
           "_FORMULA_VAR_FILE":        "CMIP6_formula_terms.json",
           "_cmip6_option":           "CMIP6",

           "tracking_prefix":        "hdl:21.14100",
           "activity_id":            "ISMIP6",


           "#output":                "Root directory where files are written",
           "outpath":                "{}",

           "#experiment_id":         "valid experiment_ids are found in CMIP6_CV.json",
           "experiment_id":          "{}",
           "sub_experiment_id":      "none",
           "sub_experiment":         "none",

           "source_type":            "AOGCM",
           "mip_era":                "CMIP6",
           "calendar":               "{}",

           "realization_index":      "{}",
           "initialization_index":   "{}",
           "physics_index":          "{}",
           "forcing_index":          "1",

           "#contact ":              "Not required",
           "contact ":              "Python Coder (coder@a.b.c.com)",

           "#history":               "not required, supplemented by CMOR",
           "history":                "Output from archivcl_A1.nce/giccm_03_std_2xCO2_2256.",

           "#comment":               "Not required",
           "comment":                "",
           "#references":            "Not required",
           "references":             "Model described by Koder and Tolkien (J. Geophys. Res., 2001, 576-591).  Also see http://www.GICC.su/giccm/doc/index.html  2XCO2 simulation described in Dorkey et al
. '(Clim. Dyn., 2003, 323-357.)'",

           "grid":                   "gs1x1",
           "grid_label":             "gr",
           "nominal_resolution":     "5 km",

           "institution_id":         "{}",

           "parent_experiment_id":   "histALL",
           "parent_activity_id":     "ISMIP6",
           "parent_mip_era":         "CMIP6",

           "parent_source_id":       "PCMDI-test-1-0",
           "parent_time_units":      "days since 1970-01-01",
           "parent_variant_label":   "r123i1p33f5",

           "branch_method":          "Spin-up documentation",
           "branch_time_in_child":   2310.0,
           "branch_time_in_parent":  12345.0,


           "#run_variant":           "Description of run variant (Recommended).",
           "run_variant":            "forcing: black carbon aerosol only",

           "#source_id":              "Model Source",
           "source_id":               "{}",

           "#source":                "source title, first part is source_id",
           "source":                 "PCMDI's PMP",


           "_history_template":       "%s ;rewrote data to be consistent with <activity_id> for variable <variable_id> found in table <table_id>.",
           "#output_path_template":   "Template for output path directory using tables keys or global attributes",
           "output_path_template":    "<mip_era><activity_id><institution_id><source_id><experiment_id><_member_id><table><variable_id><grid_label><version>",
           "output_file_template":    "<variable_id><table><source_id><experiment_id><_member_id><grid_label>",
           "license":                 "CMIP6 model data produced by Lawrence Livermore PCMDI is licensed under a Creative Commons Attribution ShareAlike 4.0 International License (https://creativecommons.org/licenses). Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse for terms of use governing CMIP6 output, including citation requirements and proper acknowledgment. Further information about this data, including some limitations, can be found via the further_info_url (recorded as a global attribute in this file) and at https:///pcmdi.llnl.gov/. The data producers and data providers make no warranty, either express or implied, including, but not limited to, warranties of merchantability and fitness for a particular purpose. All liabilities arising from the supply of the information (including any liability arising in negligence) are excluded to the fullest extent permitted by law."
}}
""".format(A.results_dir, exp, cal_name, r, i, p, inst.split()[0], src))  # noqa

    tmp.flush()
    cmor.dataset_json(tmp.name)
    if not os.path.exists(A.table):
        raise RuntimeError(
            "No such file or directory for tables: %s" % A.table)

    print("Loading table: {}".format(os.path.abspath(A.table)))
    table_content = open(A.table).read().replace("time", "time2")
    table_content = table_content.replace("time22", "time2")
    table = tempfile.NamedTemporaryFile("w")
    table.write(table_content)
    table.flush()
    for table_name in ["formula_terms", "coordinate"]:
        nm = "CMIP6_{}.json".format(table_name)
        with open(os.path.join(os.path.dirname(table.name), nm), "w") as tmp:
            tmp.write(open(os.path.join(tables_dir, nm)).read())

    table = cmor.load_table(table.name)

    # Ok CMOR is ready let's create axes
    cmor_axes = []
    for ax in s.getAxisList():
        if ax.isLatitude():
            table_entry = "latitude"
        elif ax.isLongitude():
            table_entry = "longitude"
        elif ax.isLevel():  # Need work here for sigma
            table_entry = "plevs"
        if ax.isTime():
            table_entry = "time2"
            ntimes = len(ax)
            axvals = numpy.array(values)
            axbnds = numpy.array(bounds)
            axunits = Tunits
        else:
            axvals = ax[:]
            axbnds = ax.getBounds()
            axunits = ax.units
        ax_id = cmor.axis(table_entry=table_entry,
                          units=axunits,
                          coord_vals=axvals,
                          cell_bounds=axbnds
                          )
        cmor_axes.append(ax_id)
    # Now create the variable itself
    if A.cf_var is not None:
        var_entry = A.cf_var
    else:
        var_entry = data.id

    units = A.units
    if units is None:
        units = data.units

    kw = eval(A.variable_extra_args)
    if not isinstance(kw, dict):
        raise RuntimeError(
            "invalid evaled type for -X args, should be evaled as a dict, e.g: -X '{\"positive\":\"up\"}'")
    var_id = cmor.variable(table_entry=var_entry,
                           units=units,
                           axis_ids=cmor_axes,
                           type=s.typecode(),
                           missing_value=s.missing_value,
                           **kw)

    # And finally write the data
    data2 = s.filled(s.missing_value)
    cmor.write(var_id, data2, ntimes_passed=ntimes)

    # Close cmor
    path = cmor.close(var_id, file_name=True)
    if season.lower() == "ann":
        suffix = "ac"
    else:
        suffix = season
    path2 = path.replace("-clim.nc", "-clim-%s.nc" % suffix)
    os.rename(path, path2)
    if A.verbose:
        print("Saved to:", path2)

    cmor.close()
    if A.verbose:
        print("closed cmor")


def checkCMORAttribute(att, source):
    res = getattr(A, att)
    if res is None:
        if hasattr(source, att):
            res = getattr(source, att)
        else:
            raise RuntimeError("Could not figure out the CMOR '%s'" % att)
    return res


def store_globals(file):
    globals = {}
    for att in file.listglobal():
        globals[att] = getattr(file, att)
    return globals


def store_attributes(var):
    attributes = {}
    for att in var.listattributes():
        attributes[att] = getattr(var, att)
    return attributes

def runClim(A):

    print("OK SO START IS:", A.start)
    # season dictionary
    season_function = {
        "djf": cdutil.times.DJF,
        "mam": cdutil.times.MAM,
        "jja": cdutil.times.JJA,
        "son": cdutil.times.SON,
        "ann": cdutil.times.ANNUALCYCLE,
        "year": cdutil.times.YEAR,
    }

    print("BEFORE RPOCESEED:", A.results_dir)
#   print("A VAR:", A.variable)
#   print("A REF:", A.reference)
    results_dir = A.process_templated_argument("results_dir")
    print("RESDIR:", results_dir.template)
    A.results_dir = results_dir()

    print("HERE?", os.path.join(A.modpath, A.filename_template))
    print("A.variable", A.variable, A.model)
    filename_in = A.process_templated_argument(os.path.join(A.modpath, A.filename_template))

    if A.verbose:
        print("filename in after templating:", filename_in())
    filename = glob.glob(filename_in())[0]

    if not os.path.exists(filename):
        raise RuntimeError("file '{}' doe not exits".format(filename))

    filein = cdms2.open(filename)




    fvars = list(filein.variables.keys())
    v = A.variable
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
                i0, tmp = tim.mapInterval((v0, v0), 'cob')
            except Exception:
                raise RuntimeError(
                    "Could not find value %s for start time for variable %s" %
                    (A.start, v))
        elif A.index == "date":
            v0 = A.start
            # When too close from bounds it messes it up, adding a minute seems to help
            v0 = cdtime.s2c(A.start)
            v0 = v0.add(1, cdtime.Minute)
            try:
                i0, tmp = tim.mapInterval((v0, v0), 'cob')
            except Exception:
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
                tmp, i1 = tim.mapInterval((v0, v0), 'cob')
            except Exception:
                raise RuntimeError(
                    "Could not find value %s for end time for variable %s" %
                    (A.end, v))
        elif A.index == "date":
            v0 = A.end
            # When too close from bounds it messes it up, adding a minute seems to help
            v0 = cdtime.s2c(A.end)
            v0 = v0.add(1, cdtime.Minute)
            try:
                tmp, i1 = tim.mapInterval((v0, v0), 'cob')
            except Exception:
                raise RuntimeError(
                    "Could not find end time %s for variable: %s" %
                    (A.end, v))
    # Read in data
    data = V(time=slice(i0, i1))
    if A.verbose:
        print("DATA:", data.shape, data.getTime().asComponentTime()
            [0], data.getTime().asComponentTime()[-1])
    if A.bounds:
        cdutil.times.setTimeBoundsMonthly(data)
    # Now we can actually read and compute the climo
    seasons = [s.lower() for s in A.seasons]
    if "all" in seasons:
        seasons = ["djf", "mam", "jja", "son", "year", "ann"]

    for season in seasons:
        s = season_function[season].climatology(
            data, criteriaarg=[A.threshold, None])
        g = season_function[season].get(data, criteriaarg=[A.threshold, None])
        # Ok we know we have monthly data
        # We want to tweak bounds
        T = data.getTime()
        Tg = g.getTime()
        istart = 0
        while numpy.ma.allequal(g[istart].mask, True):
            istart += 1
        iend = -1
        while numpy.ma.allequal(g[iend].mask, True):
            iend -= 1
        if iend == -1:
            iend = None
        else:
            iend += 1
        if iend is None:
            iend = len(Tg)
        Tg = Tg.subAxis(istart, iend)

        cal = T.getCalendar()
        cal_name = getCalendarName(cal)
        Tunits = T.units
        bnds = T.getBounds()
        tc = T.asComponentTime()

        if A.verbose:
            print("TG:", Tg.asComponentTime()[0])
            print("START END THRESHOLD:", istart, iend, A.threshold, len(Tg))
            # print "SEASON:", season, "ORIGINAL:", T.asComponentTime()
        b1 = cdtime.reltime(Tg.getBounds()[0][0], Tg.units)
        b2 = cdtime.reltime(Tg.getBounds()[-1][1], Tg.units)

        # First and last time points
        y1 = cdtime.reltime(Tg[0], T.units)
        y2 = cdtime.reltime(Tg[-1], T.units)

        # Mid year is:
        yr = (y2.value + y1.value) / 2.
        y = cdtime.reltime(yr, T.units).tocomp(cal).year

        if A.verbose:
            print("We found data from ", y1.tocomp(cal),
                "to", y2.tocomp(cal), "MID YEAR:", y)
            print("bounds:", b1.tocomp(cal), b2.tocomp(cal))

        values = []
        bounds = []

        # Loop thru clim month and set value and bounds appropriately
        ts = s.getTime().asComponentTime()
        for ii in range(s.shape[0]):
            t = ts[ii]
            t.year = y
            values.append(t.torel(Tunits, cal).value)
            if (s.shape[0] > 1):
                B1 = b1.tocomp(cal).add(ii, cdtime.Month)
                B2 = b2.tocomp(cal).add(ii - s.shape[0] + 1, cdtime.Month)
            else:
                B1 = b1
                B2 = b2
            # b2.year = y
            # b1.year = y
            #  if b1.cmp(b2) > 0:  # ooops
            #    if b1.month>b2.month and b1.month-b2.month!=11:
            #        b1.year -= 1
            #    else:
            #        b2.year += 1
            #  if b1.month == b2.month:
            #    b2.year = b1.year+1
            if A.verbose:
                print(B1.tocomp(cal), "<", t, "<", B2.tocomp(cal))
            bounds.append([B1.torel(Tunits, cal).value,
                        B2.torel(Tunits, cal).value])

    fnmout = genutil.StringConstructor(A.output_filename_template)

    if "model_id" in fnmout.keys():
        model_id = checkCMORAttribute("model_id")
    if "experiment_id" in fnmout.keys():
        experiment_id = checkCMORAttribute("experiment_id")
    if "realization" in fnmout.keys():
        realization = checkCMORAttribute("realization")
    if "initialization_method" in fnmout.keys():
        initialization = checkCMORAttribute("initialization_method")
    if "physics_version" in fnmout.keys():
        physics_version = checkCMORAttribute("physics_version")
    if A.cmor and hasCMOR:
        dump_cmor(A, s, values, bounds)
    else:
        if A.cmor and not hasCMOR:
            print("Your Python does not have CMOR, using regular cdms to write out files")
        if not os.path.exists(A.results_dir):
            os.makedirs(A.results_dir)
        end_tc = tc[-1].add(1, cdtime.Month)

        # Populate fout template with values
        start = "{}{:02d}".format(tc[0].year, tc[0].month)
        end = "{}{:02d}".format(end_tc.year, end_tc.month)
        for k in fnmout.keys():
            try:
                setattr(fnmout, k, getattr(A, k))
            except Exception:
                pass
            # overwrite with locals
            try:
                setattr(fnmout, k, locals()[k])
            except Exception:
                pass
        nm = os.path.join(A.results_dir, fnmout())
        f = cdms2.open(nm, "w")
        # Global attributes copied
        for att, value in store_globals(filein).items():
            setattr(f, att, value)
        t = cdms2.createAxis(values)
        t.setBounds(numpy.array(bounds))
        t.designateTime()
        t.id = "time"
        s.setAxis(0, t)
        # copy orignal attributes
        for att, value in store_attributes(V).items():
            setattr(s, att, value)
        f.write(s, dtype=data.dtype)
        f.close()
        if A.verbose:
            print("Results out to:", nm)


parameters = parser.get_parameters()

cdp.cdp_run.multiprocess(runClim, parameters)
