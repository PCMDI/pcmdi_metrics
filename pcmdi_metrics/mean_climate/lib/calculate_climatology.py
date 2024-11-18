import os
from datetime import datetime, timezone

from pcmdi_metrics.io import get_time, select_subset, xcdat_open
from pcmdi_metrics.utils import (
    check_monthly_time_axis,
    check_time_bounds_exist,
    extract_date_components,
    find_overlapping_dates,
    last_day_of_month,
    regenerate_time_axis,
)

from .plot_clim_maps import plot_climatology


# import dask


def calculate_climatology(
    var: str,
    infile: str,
    outfile: str = None,
    outpath: str = None,
    outfilename: str = None,
    outfilename_default_template: bool = True,
    start: str = None,
    end: str = None,
    ver: str = None,
    periodinname: bool = None,
    climlist: list = None,
    repair_time_axis: bool = False,
    overwrite_output: bool = True,
    save_ac_netcdf: bool = True,
    plot=True,

):
    """
    Calculate climatology from a dataset over a specified period.

    This function computes seasonal and monthly climatologies for a given variable
    in a dataset. The output can be saved to NetCDF files, with customizable options
    for file naming and output directories.

    Parameters
    ----------
    var : str
        The variable name for which the climatology is to be calculated.
    infile : str
        The path to the input dataset file(s).
    outfile : str, optional
        The base output file path (default is None).
    outpath : str, optional
        The directory to save output files (default is None, uses the directory of outfile).
    outfilename : str, optional
        The specific output filename (default is None, uses infile name).
    outfilename_default_template: bool ,optional
        Use default template to rename output file name to add information (default is True).
    start : str, optional
        The start date for the climatology period in 'YYYY-MM' format (default is None).
    end : str, optional
        The end date for the climatology period in 'YYYY-MM' format (default is None).
    ver : str, optional
        Version string for the output files (default is current date in 'vYYYYMMDD' format).
    periodinname : bool, optional
        Flag to include the time period in the output filename (default is None).
    climlist : list of str, optional
        List of climatologies to calculate and save (e.g., ["AC", "DJF", "MAM", "JJA", "SON"], default is all).
    repair_time_axis : bool, optional
        If True, regenerate time axis if data has incorrect time axis, default is False
    overwrite_output: bool, optional
        If True, output file will be overwritten regardless of its existance
    save_ac_netcdf: bool, optional
        If True, output will be saved as netcdf file(s), default is True

    Returns
    -------
    dict of xarray.Dataset
        A dictionary containing the calculated climatology datasets, with keys corresponding
        to the seasons ('DJF', 'MAM', 'JJA', 'SON') and the annual cycle ('AC').

    Notes
    -----
    - The function handles seasonal climatology for DJF (December-January-February)
      considering incomplete DJF periods.
    - The output files are saved in NetCDF format, and global attributes are preserved.

    Example
    -------
    >>> calculate_climatology(
            var='tas',
            infile='data.nc',
            outfile='climatology.nc',
            start='1980-01',
            end='1990-12',
            ver='v1',
            periodinname=True
        )
    """
    # Set version identifier using the current date if not provided
    ver = ver or datetime.now().strftime("v%Y%m%d")
    print("ver:", ver)

    # Extract the input filename from the full file path
    infilename = os.path.basename(infile)
    print("infilename:", infilename)

    # Open the dataset using xcdat's open_mfdataset function
    ds = xcdat_open(infile, data_var=var)
    print("type(d):", type(ds))

    atts = d.attrs
    print("atts:", atts)  # Print dataset attributes

    # Check if dataset time axis is okay
    try:
        check_monthly_time_axis(ds)
    except ValueError:
        print(f"Error: time axis error from {infilename}")
        if repair_time_axis:
            ds = regenerate_time_axis(ds)

    # check if time bounds data exists
    try:
        check_time_bounds_exist(ds)
    except ValueError:
        print(f"Error: time bounds missing from {infilename}")
        if repair_time_axis:
            ds = ds.bounds.add_missing_bounds(["T"])
            print("Generated time bounds")

    if len(get_time(ds)) == 12:
        input_is_annual_cycle = True
        dec_mode = "JFD"
    else:
        input_is_annual_cycle = False
        dec_mode = "DJF"

    # Determine the output directory, using outpath if provided, else use the directory of outfile
    outdir = outpath or os.path.dirname(outfile)
    os.makedirs(outdir, exist_ok=True)  # Create the directory if it doesn't exist
    print("outdir:", outdir)

    # Define the climatology period based on the provided start and end dates, or use the entire time series
    if start is not None and end is not None and not input_is_annual_cycle:
        # If a period is specified by the user, parse the start and end dates
        start_yr, start_mo = map(int, start.split("-")[:2])
        start_da = 1  # Default to the first day of the start month
        end_yr, end_mo = map(int, end.split("-")[:2])
        # Determine the last day of the end month
        end_da = last_day_of_month(end_yr, end_mo)

        # Format the start and end dates as strings (YYYY-MM-DD)
        start_str = f"{start_yr:04d}-{start_mo:02d}-{start_da:02d}"
        end_str = f"{end_yr:04d}-{end_mo:02d}-{end_da:02d}"

        # Update start and end dates strings to those overlaps with the actual dataset
        start_str, end_str = find_overlapping_dates(ds, start_str, end_str)

        # Adjust start_str and end_str to fit calendar year if needed
        start_yr, start_mo = map(int, start_str.split("-")[:2])
        end_yr, end_mo = map(int, end_str.split("-")[:2])

        if start_mo != 1:
            start_yr += 1
            start_mo = 1
            start_da = 1
            start_str = f"{start_yr:04d}-{start_mo:02d}-{start_da:02d}"

        if end_mo != 12:
            end_yr -= 1
            end_mo = 12
            end_da = 31
            end_str = f"{end_yr:04d}-{end_mo:02d}-{end_da:02d}"

        # Subset the dataset to the selected time period
        ds = select_subset(ds, time=(start_str, end_str))

    # Extract the start and end year, month, and day from the dataset time coordinate
    start_yr, start_mo, start_da = extract_date_components(ds, index=0)
    end_yr, end_mo, end_da = extract_date_components(ds, index=-1)

    print(f"start: {start_yr:04d}-{start_mo:02d}-{start_da:02d}")
    print(f"end: {end_yr:04d}-{end_mo:02d}-{end_da:02d}")

    # Determine which climatologies to process, defaulting to all if none are specified
    seasons = climlist or ["AC", "DJF", "MAM", "JJA", "SON"]

    # Find the first element except "AC"
    first_season = next(item for item in seasons if item != "AC")

    # Create a dictionary as pointer to climatology fields
    ds_clim_dict = dict()

    season_index_dict = {"DJF": 0, "MAM": 1, "JJA": 2, "SON": 3}

    print("outdir, outfilename, outfile:", outdir, outfilename, outfile)

    # Iterate over the selected climatologies and save each to a NetCDF file
    for s in seasons:
        if outfilename_default_template:
            # Define the output filename suffix based on the climatology and period (if specified)
            addf = (
                f".{start_yr:04d}{start_mo:02d}-{end_yr:04d}{end_mo:02d}.{s}.{ver}.nc"
                if periodinname
                else f".{s}.{ver}.nc"
            )
            # Replace the .nc extension in the base output file with the defined suffix
            if outfilename is not None:
                outpath_season = os.path.join(outdir, outfilename.replace(".nc", addf))
            elif outfile is not None:
                outpath_season = os.path.join(
                    outdir, str(os.path.basename(outfile)).replace(".nc", addf)
                )
            else:
                outpath_season = os.path.join(
                    outdir, str(os.path.basename(infile)).replace(".nc", addf)
                )
        else:
            outpath_season = os.path.join(
                outdir,
                outfilename.replace(
                    "%(start-yyyymm)-%(end-yyyymm)",
                    f"{start_yr:04d}{start_mo:02d}-{end_yr:04d}{end_mo:02d}",
                ).replace("%(season)", s),
            )

        if not os.path.isfile(outpath_season) or overwrite_output:
            # Handle the "AC" (Annual Cycle) case
            if s == "AC":
                ds_ac = (
                    ds
                    if input_is_annual_cycle
                    else ds.temporal.climatology(var, freq="month", weighted=True)
                )
                ds_clim_s = ds_ac

            # Handle the first season and subsequent seasons
            else:
                # (Optional) Configure Dask for large chunk processing if necessary
                # dask.config.set(**{"array.slicing.split_large_chunks": True})  # Uncomment if needed

                # Compute seasonal climatology (weighted) with specific settings for DJF
                if s == first_season:
                    ds_clim = ds.temporal.climatology(
                        var,
                        freq="season",
                        weighted=True,
                        season_config={
                            "dec_mode": dec_mode,
                            "drop_incomplete_djf": True,
                        },
                    )

                ds_clim_s = ds_clim.isel(time=season_index_dict[s])

            # Prepare annual or seasonal climatology for the next step

            # Get the current time with UTC timezone
            current_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            ds_clim_s = ds_clim_s.assign_attrs(
                current_date=f"{current_time_utc}",
                history=f"{current_time_utc}; PCMDI Metrics Package (PMP) calculated climatology using {infilename}",
                filename=os.path.basename(outpath_season),
            )

            # Save the climatology file unless it's an annual cycle input and "AC"
            if save_ac_netcdf:
                if s != "AC" or not input_is_annual_cycle:
                    # Save climatology to the output NetCDF file, including global attributes
                    ds_clim_s.to_netcdf(outpath_season)
                    print(
                        f"Successfully saved climatology for season '{s}' to {outpath_season}"
                    )
                else:
                    print("Skipping 'AC' as input is already an annual cycle.")

            # Add annual or seasonal climatology to the dictionary
            ds_clim_dict[s] = ds_clim_s


        print("output file is", out_season)
        d_clim_dict[s].to_netcdf(
            out_season
        )  # global attributes are automatically saved as well

        if plot and s == "AC":
            plot_climatology(
                d_ac,
                var,
                season_to_plot="all",
                output_filename=out_season.replace(".nc", ".png"),
            )

    ds.close()
    return ds_clim_dict  # Return the dictionary of all climatology datasets
  