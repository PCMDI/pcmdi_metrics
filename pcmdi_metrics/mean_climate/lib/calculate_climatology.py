import datetime
import os

import dask

from pcmdi_metrics.io import xcdat_open, select_subset
from pcmdi_metrics.utils import check_monthly_time_axis, find_overlapping_dates


def calculate_climatology(
    var: str,
    infile: str,
    outfile: str=None,
    outpath: str=None,
    outfilename: str=None,
    start: str=None,
    end: str=None,
    ver: str=None,
    periodinname: bool=None,
    climlist: list=None,
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
    ver = ver or datetime.datetime.now().strftime("v%Y%m%d")
    print("ver:", ver)

    # Extract the input filename from the full file path
    infilename = os.path.basename(infile)
    print("infilename:", infilename)

    # Open the dataset using xcdat's open_mfdataset function
    ds = xcdat_open(infile, data_var=var)
    print("type(d):", type(ds))
    print("atts:", ds.attrs)  # Print dataset attributes

    # Check if dataset time axis is okay
    check_monthly_time_axis(ds)

    # Determine the output directory, using outpath if provided, else use the directory of outfile
    outdir = outpath or os.path.dirname(outfile)
    os.makedirs(outdir, exist_ok=True)  # Create the directory if it doesn't exist
    print("outdir:", outdir)

    # Define the climatology period based on the provided start and end dates, or use the entire time series
    if start is not None and end is not None:
        # Extract the start and end year, month, and day from the dataset time coordinate
        start_yr, start_mo, start_da = extract_date_components(ds, index=0)
        end_yr, end_mo, end_da = extract_date_components(ds, index=-1)
    else:
        # If a period is specified by the user, parse the start and end dates
        start_yr, start_mo = map(int, start.split("-")[:2])
        start_da = 1  # Default to the first day of the start month
        end_yr, end_mo = map(int, end.split("-")[:2])
        # Determine the last day of the end month
        end_da = int(
            ds.time.dt.days_in_month.sel(time=ds.time.dt.year == end_yr)[end_mo - 1]
        )

    # Format the start and end dates as strings (YYYY-MM-DD)
    start_str = f"{start_yr:04d}-{start_mo:02d}-{start_da:02d}"
    end_str = f"{end_yr:04d}-{end_mo:02d}-{end_da:02d}"

    # Update start and end dates strings to those overlaps with the actual dataset
    start_str, end_str = find_overlapping_dates(ds, start_str, end_str)

    # Subset the dataset to the selected time period
    ds = select_subset(ds, time=(start_str, end_str))

    print("start_str:", start_str)
    print("end_str:", end_str)

    # Configure Dask to handle large chunks and calculate climatology
    # dask.config.set(**{"array.slicing.split_large_chunks": True})
    # Compute seasonal climatology (weighted)
    ds_clim = ds.temporal.climatology(
        var,
        freq="season",
        weighted=True,
        season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},
    )
    # Compute monthly climatology (weighted)
    ds_ac = ds.temporal.climatology(var, freq="month", weighted=True)

    # Organize the computed climatologies into a dictionary
    ds_clim_dict = {
        season: ds_clim.isel(time=i)
        for i, season in enumerate(["DJF", "MAM", "JJA", "SON"])
    }
    ds_clim_dict["AC"] = ds_ac  # Add the annual cycle climatology

    # Determine which climatologies to process, defaulting to all if none are specified
    clims = climlist or ["AC", "DJF", "MAM", "JJA", "SON"]

    print("outdir, outfilename, outfile:", outdir, outfilename, outfile)

    # Iterate over the selected climatologies and save each to a NetCDF file
    for s in clims:
        # Define the output filename suffix based on the climatology and period (if specified)
        addf = (
            f".{start_yr:04d}{start_mo:02d}-{end_yr:04d}{end_mo:02d}.{s}.{ver}.nc"
            if periodinname
            else f".{s}.{ver}.nc"
        )
        # Replace the .nc extension in the base output file with the defined suffix
        if outfilename is not None:
            outpath_season = os.path.join(outdir, outfilename.replace(".nc", addf))
        elif  outfile is not None:
            outpath_season = os.path.join(outdir, str(os.path.basename(outfile)).replace(".nc", addf))
        else:
            outpath_season = os.path.join(outdir, str(os.path.basename(infile)).replace(".nc", addf))

        print(f"output file for {s} is {outpath_season}")
        # Save the climatology to the output NetCDF file, including global attributes
        ds_clim_dict[s].to_netcdf(outpath_season)

    return ds_clim_dict  # Return the dictionary of all climatology datasets



def extract_date_components(ds, index=0):
    date = ds.time.values[index]
    return date.year, date.month, date.day


