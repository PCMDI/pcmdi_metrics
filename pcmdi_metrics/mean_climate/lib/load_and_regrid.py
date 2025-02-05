import numpy as np
import xarray as xr
import xcdat as xc

from pcmdi_metrics.io import get_latitude, get_longitude, xcdat_open


def load_and_regrid(
    data_path,
    varname,
    varname_in_file=None,
    level=None,
    t_grid=None,
    decode_times=True,
    regrid_tool="regrid2",
    calendar_qc=False,
    debug=False,
):
    """Load data and regrid to target grid

    Args:
        data_path (str): full data path for nc or xml file
        varname (str): variable name
        varname_in_file (str): variable name if data array named differently
        level (float): level to extract (unit in hPa)
        t_grid (xarray.core.dataset.Dataset): target grid to regrid
        decode_times (bool): Default is True. decode_times=False will be removed once obs4MIP written using xcdat
        regrid_tool (str): Name of the regridding tool. See https://xcdat.readthedocs.io/en/stable/generated/xarray.Dataset.regridder.horizontal.html for more info
        calendar_qc (bool): Turn on QC for calendar. Default is False.
        debug (bool): Default is False. If True, print more info to help debugging process
    """
    if debug:
        print("load_and_regrid start")

    if varname_in_file is None:
        varname_in_file = varname

    # load data
    ds = xcdat_open(
        data_path, data_var=varname_in_file, decode_times=decode_times
    )  # NOTE: decode_times=False will be removed once obs4MIP written using xcdat

    # SET CONDITIONAL ON INPUT VARIABLE
    if varname == "pr":
        print("Adjust units for pr")
        if "units" in ds[varname_in_file].attrs:
            if ds[varname_in_file].units == "kg m-2 s-1":
                ds[varname_in_file] = ds[varname_in_file] * 86400
                print(
                    "pr units adjusted to [mm d-1] from [kg m-2 s-1] by 86400 multiplied"
                )
        else:
            ds[varname_in_file] = ds[varname_in_file] * 86400  # Assumed as kg m-2 s-1
        ds.attrs["units"] = "mm/day"

    if calendar_qc:
        # calendar quality check
        if "calendar" in list(ds.time.attrs.keys()):
            if debug:
                print('ds.time.attrs["calendar"]:', ds.time.attrs["calendar"])
            if "calendar" in ds.attrs.keys():
                if debug:
                    print("ds.calendar:", ds.calendar)
                if ds.calendar != ds.time.attrs["calendar"]:
                    ds.time.encoding["calendar"] = ds.calendar
                    print(
                        '[WARNING]: calendar info mismatch. ds.time.attrs["calendar"] is adjusted to ds.calendar, ',
                        ds.calendar,
                    )
        else:
            if "calendar" in ds.attrs.keys():
                ds.time.attrs["calendar"] = ds.calendar
                print(
                    '[WARNING]: calendar info not found for time axis. ds.time.attrs["calendar"] is adjusted to ds.calendar, ',
                    ds.calendar,
                )
            else:
                ds.time.attrs["calendar"] = "standard"
                print(
                    '[WARNING]: calendar info not found for time axis. ds.time.attrs["calendar"] is adjusted to standard'
                )

    # time bound check #1 -- add proper time bound info if non-xcdat-generated annual cycle is loaded
    if isinstance(
        ds.time.values[0], np.float64
    ):  # and "units" not in list(ds.time.attrs.keys()):
        ds.time.attrs["units"] = "days since 0001-01-01"
        ds = xc.decode_time(ds)
        if debug:
            print("decode_time done")

    # time bound check #2 -- add time bounds itself it it is missing
    if "bounds" in list(ds.time.attrs.keys()):
        time_bnds_key = ds.time.attrs["bounds"]
        if time_bnds_key not in list(ds.keys()):
            ds = ds.bounds.add_missing_bounds(["T"])
            print("[WARNING]: bounds.add_missing_bounds conducted for T axis")

    # extract level
    if level is not None:
        ds = extract_level(ds, level, debug=debug)

    # axis
    lat = get_latitude(ds)
    lon = get_longitude(ds)
    if "axis" not in lat.attrs:
        ds[lat.name].attrs["axis"] = "Y"
    if "axis" not in lon.attrs:
        ds[lon.name].attrs["axis"] = "X"

    # regrid
    if regrid_tool == "regrid2":
        ds_regridded = ds.regridder.horizontal(
            varname_in_file, t_grid, tool=regrid_tool
        )
    elif regrid_tool in ["esmf", "xesmf"]:
        regrid_tool = "xesmf"
        regrid_method = "bilinear"
        ds_regridded = ds.regridder.horizontal(
            varname_in_file, t_grid, tool=regrid_tool, method=regrid_method
        )

    if varname != varname_in_file:
        ds_regridded[varname] = ds_regridded[varname_in_file]
        ds_regridded = ds_regridded.drop_vars([varname_in_file])

    # preserve units in regridded dataset
    try:
        units = ds.attrs["units"] or ds[varname].units
    except Exception as e:
        print(e)
        units = ""
    print("units:", units)

    ds_regridded[varname] = ds_regridded[varname].assign_attrs({"units": units})

    # time bound check #3 -- preserve time bnds in regridded dataset
    if "bounds" in list(ds_regridded.time.attrs.keys()):
        time_bnds_key = ds_regridded.time.attrs["bounds"]
        if time_bnds_key not in list(ds_regridded.keys()):
            ds_regridded = ds_regridded.bounds.add_missing_bounds(["T"])
            print("[WARNING]: bounds.add_missing_bounds conducted for T axis")

    if debug:
        print("ds_regridded:", ds_regridded)
    return ds_regridded


def extract_level(ds: xr.Dataset, level, debug=False):
    """_summary_

    Args:
        ds (xr.Dataset): _description_
        level (_type_): level, hPa
        debug (bool, optional): _description_. Defaults to False.
    """

    def find_nearest(array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]

    # level - extract a specific level if needed
    if level is not None:
        if isinstance(level, int) or isinstance(level, float):
            pass
        else:
            level = float(level)

        # check vertical coordinate first
        if "plev" in list(ds.coords.keys()):
            units_in_data = None
            if "units" in ds.plev.attrs:
                if ds.plev.units == "Pa":
                    units_in_data = "Pa"
            else:
                if max(ds.plev.values) > 10000:
                    units_in_data = "Pa"

            if units_in_data == "Pa":
                level = level * 100  # hPa to Pa

            try:
                ds = ds.sel(plev=level)
            except Exception as ex:
                print("WARNING: ", ex)

                nearest_level = find_nearest(ds.plev.values, level)

                print("  Given level", level)
                print("  Selected nearest level from dataset:", nearest_level)

                diff_percentage = abs(nearest_level - level) / level * 100
                if diff_percentage < 0.1:  # acceptable if differance is less than 0.1%
                    ds = ds.sel(plev=level, method="nearest")
                    print("  Difference is in acceptable range.")
                    pass
                else:
                    raise ValueError(
                        "ERROR: Difference between two levels are too big!"
                    )
            if debug:
                print("ds:", ds)
                # print("ds.plev.units:", ds.plev.units)
        else:
            raise ValueError(
                "ERROR: plev is not in the nc file. Check vertical coordinate.\n"
                + f"Coordinates keys in the nc file: {list(ds.coords.keys())}\n"
                + "ERROR: load and regrid can not complete"
            )

        return ds
