#!/usr/bin/env python
import datetime
import os

from genutil import StringConstructor

import pcmdi_metrics
from pcmdi_metrics.io import xcdat_open


def clim_calc_x(var, infile, outfile=None, outpath=None, outfilename=None, start=None, end=None):

    ver = datetime.datetime.now().strftime("v%Y%m%d")
    print('time is ', ver)

    tmp = infile.split("/")
    infilename = tmp[len(tmp) - 1]
    print("infilename is ", infilename)

    # d = xcdat.open_dataset(infile, data_var=var)
    d = xcdat_open(infile, data_var=var)
    atts = d.attrs

    print('type(d):', type(d))
    print('atts:', atts)

    # CONTROL OF OUTPUT DIRECTORY AND FILE
    out = outfile
    if outpath is None:
        outdir = os.path.dirname(outfile)
    else:
        outdir = outpath
    os.makedirs(outdir, exist_ok=True)

    print("outdir is ", outdir)

    c = d.time
    # print(c)

    # CLIM PERIOD
    if (start is None) and (end is None):
        # DEFAULT CLIM - BASED ON ENTIRE TIME SERIES
        start_yr_str = str(int(c["time.year"][0]))
        start_mo_str = str(int(c["time.month"][0]).zfill(2))
        end_yr_str = str(int(c["time.year"][len(c) - 1]))
        end_mo_str = str(int(c["time.month"][len(c) - 1]).zfill(2))
        start_yr = int(start_yr_str)
        start_mo = int(start_mo_str)
        end_yr = int(end_yr_str)
        end_mo = int(end_mo_str)
        print(start_yr_str, start_mo_str, end_yr_str, end_mo_str)
    else:
        # USER DEFINED PERIOD
        start_yr = int(start.split("-")[0])
        start_mo = int(start.split("-")[1])
        end_yr = int(end.split("-")[0])
        end_mo = int(end.split("-")[1])
        start_yr_str = str(start_yr)
        start_mo_str = str(start_mo).zfill(2)
        end_yr_str = str(end_yr)
        end_mo_str = str(end_mo).zfill(2)

    d = d.sel(time=slice(start_yr_str + '-' + start_mo_str + '-01',
                         end_yr_str + '-' + end_mo_str + '-31'))
    # print(d)

    print("start_yr_str is ", start_yr_str)
    print("start_mo_str is ", start_mo_str)
    print("end_yr_str is ", end_yr_str)
    print("end_mo_str is ", end_mo_str)

    start_mo_str = start_mo_str.zfill(2)
    end_mo_str = end_mo_str.zfill(2)

    d_clim = d.temporal.climatology(var, freq="season", weighted=True, season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},)

    d_clim_dict = dict()

    d_clim_dict['DJF'] = d_clim.isel(time=0)
    d_clim_dict['MAM'] = d_clim.isel(time=1)
    d_clim_dict['JJA'] = d_clim.isel(time=2)
    d_clim_dict['SON'] = d_clim.isel(time=3)

    d_ac = d.temporal.climatology(var, freq="month", weighted=True)
    print('below ac')

    d_clim_dict['AC'] = d_ac

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
        if outfilename is not None:
            out = os.path.join(outdir, outfilename)
        out_season = out.replace(".nc", addf)

        print("out_season is ", out_season)
        d_clim_dict[s].to_netcdf(out_season)


if __name__ == "__main__":

    ver = datetime.datetime.now().strftime("v%Y%m%d")

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

        print('var:', var)
        print('infile:', infile)
        print('outfile:', outfile)
        print('outfilename:', outfilename)
        print('outpath:', outpath)

        # calculate climatologies for this variable
        clim_calc_x(var, infile, outfile, outpath, outfilename, start, end)
