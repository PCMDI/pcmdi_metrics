#!/usr/bin/env python
import datetime

import cdms2
from genutil import StringConstructor

import pcmdi_metrics

ver = datetime.datetime.now().strftime("v%Y%m%d")

cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

#

def clim_calc_x(var, infile, outfile, outpath, outfilename, start, end):
    import datetime
    import os
    import xcdat
    import xarray

    ver = datetime.datetime.now().strftime("v%Y%m%d")
    print('time is ', ver)

    lf = infile
    tmp = lf.split("/")
    infilename = tmp[len(tmp) - 1]
    print("infilename is ", infilename)

    d = xcdat.open_dataset(lf, data_var=var)
    atts = d.attrs
    outfd = outfile
    outdir = os.path.dirname(outfd)

    print(type(d))
    print(atts)
    print(outfd)
    print(outdir)
    print('done')

# CONTROL OF OUTPUT DIRECTORY AND FILE

    print("outfd is ", outfd)
#   print("outdir is ", outdir)

    seperate_clims = "y"

    c = d.time
#   print(c)

# DEFAULT CLIM - BASED ON ENTIRE TIME SERIES
    if (start is None) and (end is None):
        start_yr_str = str(int(c["time.year"][0])) 
        start_mo_str = str(int(c["time.month"][0])) 
        end_yr_str = str(int(c["time.year"][len(c) - 1]))
        end_mo_str = str(int(c["time.month"][len(c) - 1]))
        start_yr = int(start_yr_str)
        start_mo = int(start_mo_str)
        end_yr = int(end_yr_str)
        end_mo = int(end_mo_str)
        print(start_yr_str,start_mo_str,end_yr_str,end_mo_str)

# USER DEFINED PERIOD
    else:
        start_mo = int(start.split("-")[1])
        start_yr = int(start.split("-")[0])
        end_mo = int(end.split("-")[1])
        end_yr = int(end.split("-")[0])
        start_yr_str = str(start_yr)
        start_mo_str = str(start_mo)
        end_yr_str = str(end_yr)
        end_mo_str = str(end_mo)

    d = d.sel(time=slice(start_yr_str + '-' + start_mo_str, end_yr_str + '-' + end_mo_str))
#   print(d)

    print("start_yr_str is ", start_yr_str)

    if start_mo_str not in ["11", "12"]:
        start_mo_str = "0" + start_mo_str
    if end_mo_str not in ["11", "12"]:
        end_mo_str = "0" + end_mo_str

    d_djf = d.temporal.climatology(var, freq="season", weighted=True, season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},).isel(time=slice(0, 1))
    d_mam = d.temporal.climatology(var, freq="season", weighted=True, season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},).isel(time=slice(1, 2))
    d_jja = d.temporal.climatology(var, freq="season", weighted=True, season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},).isel(time=slice(2, 3))
    d_son = d.temporal.climatology(var, freq="season", weighted=True, season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},).isel(time=slice(3, 4))
    d_ac =  d.temporal.climatology(var, freq="month", weighted=True) 


    print(d_son)
    print(d_ac)




#####


def clim_calc(var, infile, outfile, outdir, outfilename, start, end):
    import datetime
    import os

    import cdms2
    import cdtime
    import cdutil

    ver = datetime.datetime.now().strftime("v%Y%m%d")

    lf = infile
    tmp = lf.split("/")
    infilename = tmp[len(tmp) - 1]
    print("infilename is ", infilename)

    f = cdms2.open(lf)
    atts = f.listglobal()
    outfd = outfile

    # CONTROL OF OUTPUT DIRECTORY AND FILE

    # outdir AND outfilename PROVIDED BY USER
    if outdir is not None and outfilename is not None:
        outfd = outdir + outfilename

    # outdir PROVIDED BY USER, BUT filename IS TAKEN FROM infilename WITH CLIM MODIFICATIONS SUFFIX ADDED BELOW
    if outdir is not None and outfilename is None:
        outfd = outdir + "/" + infilename

    if outdir is None and outfilename is None:
        outfd = outfile

    print("outfd is ", outfd)
    print("outdir is ", outdir)

    seperate_clims = "y"

    # DEFAULT CLIM - BASED ON ENTIRE TIME SERIES
    if (start is None) and (end is None):
        d = f(var)
        t = d.getTime()
        c = t.asComponentTime()
        start_yr_str = str(c[0].year)
        start_mo_str = str(c[0].month)
        end_yr_str = str(c[len(c) - 1].year)
        end_mo_str = str(c[len(c) - 1].month)
        start_yr = int(start_yr_str)
        start_mo = int(start_mo_str)
        end_yr = int(end_yr_str)
        end_mo = int(end_mo_str)

    # USER DEFINED PERIOD
    else:
        start_mo = int(start.split("-")[1])
        start_yr = int(start.split("-")[0])
        end_mo = int(end.split("-")[1])
        end_yr = int(end.split("-")[0])
        start_yr_str = str(start_yr)
        start_mo_str = str(start_mo)
        end_yr_str = str(end_yr)
        end_mo_str = str(end_mo)

    d = f(
        var, time=(cdtime.comptime(start_yr, start_mo), cdtime.comptime(end_yr, end_mo))
    )

    print("start_yr_str is ", start_yr_str)

    if start_mo_str not in ["11", "12"]:
        start_mo_str = "0" + start_mo_str
    if end_mo_str not in ["11", "12"]:
        end_mo_str = "0" + end_mo_str

    d_ac = cdutil.ANNUALCYCLE.climatology(d).astype("float32")
    d_djf = cdutil.DJF.climatology(d)(squeeze=1).astype("float32")
    d_jja = cdutil.JJA.climatology(d)(squeeze=1).astype("float32")
    d_son = cdutil.SON.climatology(d)(squeeze=1).astype("float32")
    d_mam = cdutil.MAM.climatology(d)(squeeze=1).astype("float32")

    for v in [d_ac, d_djf, d_jja, d_son, d_mam]:

        v.id = var

    for s in ["AC", "DJF", "MAM", "JJA", "SON"]:

        addf = (
            "."
            + start_yr_str
            + start_mo_str
            + "-"
            + end_yr_str
            + end_mo_str
            + "."
            + s
            + "."
            + ver
            + ".nc"
        )

        if seperate_clims == "y":
            print("outfd is ", outfd)
            out = outfd
            out = out.replace(".nc", addf)
            out = out.replace(".xml", addf)
            print("out is ", out)

        if seperate_clims == "n":
            out = outfd.replace("climo.nc", s + ".nc")
        if s == "AC":
            do = d_ac
        if s == "DJF":
            do = d_djf
        if s == "MAM":
            do = d_mam
        if s == "JJA":
            do = d_jja
        if s == "SON":
            do = d_son
        do.id = var

        #  MKDIRS AS NEEDED
        lst = outfd.split("/")
        s = "/"
        for ll in range(len(lst)):
            d = s.join(lst[0 : ll + 1])
            try:
                os.mkdir(d)
            except OSError:
                pass

        g = cdms2.open(out, "w+")
        g.write(do)

        for att in atts:
            setattr(g, att, f.getglobal(att))
        g.close()
        print(do.shape, " ", d_ac.shape, " ", out)
        f.close()
    return


#######################################################################


P = pcmdi_metrics.driver.pmp_parser.PMPMetricsParser()


P.add_argument(
    "--vars", dest="vars", help="List of variables", nargs="+", required=False
)
P.add_argument("--infile", dest="infile", help="Defines infile", required=False)
P.add_argument(
    "--outfile", dest="outfile", help="Defines output path and filename", required=False
)
P.add_argument("--outpath", dest="outpath", help="Defines outpath only", required=False)
P.add_argument(
    "--outfilename",
    dest="outfilename",
    help="Defines out filename only",
    required=False,
)
P.add_argument(
    "--start", dest="start", help="Defines start year and month", required=False
)
P.add_argument("--end", dest="end", help="Defines end year and month", required=False)

args = P.get_parameter()

infile_template = args.infile
outfile_template = args.outfile
outpath_template = args.outpath
outfilename_template = args.outfilename
varlist = args.vars
start = args.start
end = args.end

print("start and end are ", start, " ", end)
print("variable list: ", varlist)

InFile = StringConstructor(infile_template)
OutFile = StringConstructor(outfile_template)
OutFileName = StringConstructor(outfilename_template)
OutPath = StringConstructor(outpath_template)

for var in varlist:
    # Build filenames
    InFile.variable = var
    OutFile.variable = var
    OutFileName.variable = var
    OutPath.variable = var
    infile = InFile()
    outfile = OutFile()
    outfilename = OutFileName()
    outpath = OutPath()

    # calculate climatologies for this variable
    clim_calc_x(var, infile, outfile, outpath, outfilename, start, end)
