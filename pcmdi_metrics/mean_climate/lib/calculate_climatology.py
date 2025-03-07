import datetime
import os

import dask

from pcmdi_metrics.io import xcdat_open

from .plot_clim_maps import plot_climatology


def calculate_climatology(
    var,
    infile,
    outfile=None,
    outpath=None,
    outfilename=None,
    start=None,
    end=None,
    ver=None,
    periodinname=None,
    climlist=None,
    plot=True,
):
    if ver is None:
        ver = datetime.datetime.now().strftime("v%Y%m%d")

    print("ver:", ver)

    infilename = infile.split("/")[-1]
    print("infilename:", infilename)

    # open file
    d = xcdat_open(infile, data_var=var)
    atts = d.attrs

    print("type(d):", type(d))
    print("atts:", atts)

    # CONTROL OF OUTPUT DIRECTORY AND FILE
    out = outfile
    if outpath is None:
        outdir = os.path.dirname(outfile)
    else:
        outdir = outpath
    os.makedirs(outdir, exist_ok=True)

    print("outdir:", outdir)

    # CLIM PERIOD
    if (start is None) and (end is None):
        # DEFAULT CLIM - BASED ON ENTIRE TIME SERIES
        start_yr = int(d.time["time.year"][0])
        start_mo = int(d.time["time.month"][0])
        start_da = int(d.time["time.day"][0])
        end_yr = int(d.time["time.year"][-1])
        end_mo = int(d.time["time.month"][-1])
        end_da = int(d.time["time.day"][-1])
    else:
        # USER DEFINED PERIOD
        start_yr = int(start.split("-")[0])
        start_mo = int(start.split("-")[1])
        start_da = 1
        end_yr = int(end.split("-")[0])
        end_mo = int(end.split("-")[1])
        end_da = int(
            d.time.dt.days_in_month.sel(time=(d.time.dt.year == end_yr))[end_mo - 1]
        )

    start_yr_str = str(start_yr).zfill(4)
    start_mo_str = str(start_mo).zfill(2)
    start_da_str = str(start_da).zfill(2)
    end_yr_str = str(end_yr).zfill(4)
    end_mo_str = str(end_mo).zfill(2)
    end_da_str = str(end_da).zfill(2)

    # Subset given time period
    d = d.sel(
        time=slice(
            f"{start_yr_str}-{start_mo_str}-{start_da_str}",
            f"{end_yr_str}-{end_mo_str}-{end_da_str}",
        )
    )

    print("start_yr_str is ", start_yr_str)
    print("start_mo_str is ", start_mo_str)
    print("end_yr_str is ", end_yr_str)
    print("end_mo_str is ", end_mo_str)

    # Calculate climatology
    dask.config.set(**{"array.slicing.split_large_chunks": True})
    d_clim = d.temporal.climatology(
        var,
        freq="season",
        weighted=True,
        season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},
    )
    d_ac = d.temporal.climatology(var, freq="month", weighted=True)

    d_clim_dict = dict()

    d_clim_dict["DJF"] = d_clim.isel(time=0)
    d_clim_dict["MAM"] = d_clim.isel(time=1)
    d_clim_dict["JJA"] = d_clim.isel(time=2)
    d_clim_dict["SON"] = d_clim.isel(time=3)
    d_clim_dict["AC"] = d_ac

    if climlist is None:
        clims = ["AC", "DJF", "MAM", "JJA", "SON"]
    else:
        clims = climlist

    for s in clims:
        # Save to netcdf file
        if periodinname is None:
            addf = (
                f".{start_yr_str}{start_mo_str}-{end_yr_str}{end_mo_str}.{s}.{ver}.nc"
            )
        if periodinname is not None:
            addf = "." + s + "." + ver + ".nc"

        if outfilename is not None:
            out = os.path.join(outdir, outfilename)

        out_season = out.replace(".nc", addf)

        d_clim_dict[s].to_netcdf(
            out_season
        )  # global attributes are automatically saved as well

        print("output file:", out_season)

        # Plot climatology
        if plot and s == "AC":
            # Check if variable is 4D
            if is_4d_variable(d_ac, var):
                # Plot 3 levels (hPa) for 4D variables for quick check
                levels_to_plot = [200, 500, 850]
            else:
                levels_to_plot = [None]

            # Plot climatology for each level
            for level in levels_to_plot:
                output_fig_path = out_season.replace(".nc", ".png")
                if level is not None:
                    if var in output_fig_path:
                        output_fig_path = os.path.join(
                            outdir,
                            output_fig_path.split("/")[-1].replace(
                                var, f"{var}-{level}"
                            ),
                        )
                    else:
                        output_fig_path = output_fig_path.replace(
                            ".png", f"-{level}.png"
                        )

                # plot climatology for each level
                plot_climatology(
                    d_ac,
                    var,
                    level=level,
                    season_to_plot="all",
                    output_filename=output_fig_path,
                    period=f"{start_yr_str}-{end_yr_str}",
                )

                print("output figure:", output_fig_path)


def is_4d_variable(ds, data_var):
    da = ds[data_var]
    print("data_var, da.shape:", data_var, da.shape)
    return len(da.shape) == 4
