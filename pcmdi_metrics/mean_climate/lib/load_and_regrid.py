import cftime
import numpy as np
import xcdat as xc

from pcmdi_metrics.io import xcdat_open


def load_and_regrid(
    data_path,
    varname,
    varname_in_file=None,
    level=None,
    t_grid=None,
    decode_times=True,
    regrid_tool="regrid2",
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

    # calendar quality check
    if "calendar" in list(ds.time.attrs.keys()):
        if debug:
            print('ds.time.attrs["calendar"]:', ds.time.attrs["calendar"])
        if "calendar" in ds.attrs.keys():
            if debug:
                print("ds.calendar:", ds.calendar)
            if ds.calendar != ds.time.attrs["calendar"]:
                print(
                    '[WARNING]: calendar info mismatch. ds.time.attrs["calendar"] is adjusted to ds.calendar'
                )
                ds.time.attrs["calendar"] = ds.calendar
    else:
        if "calendar" in ds.attrs.keys():
            ds.time.attrs["calendar"] = ds.calendar

    # time bound check -- add proper time bound info if cdms-generated annual cycle is loaded
    if isinstance(
        ds.time.values[0], np.float64
    ):  # and "units" not in list(ds.time.attrs.keys()):
        ds.time.attrs["units"] = "days since 0001-01-01"
        ds = xc.decode_time(ds)
        if debug:
            print("decode_time done")

    # level - extract a specific level if needed
    if level is not None:
        if isinstance(level, int) or isinstance(level, float):
            pass
        else:
            level = float(level)

        # check vertical coordinate first
        if "plev" in list(ds.coords.keys()):
            if ds.plev.units == "Pa":
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
                    print("ERROR: Difference between two levels are too big!")
                    return
            if debug:
                print("ds:", ds)
                print("ds.plev.units:", ds.plev.units)
        else:
            print("ERROR: plev is not in the nc file. Check vertical coordinate.")
            print("  Coordinates keys in the nc file:", list(ds.coords.keys()))
            print("ERROR: load and regrid can not complete")
            return

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

    # preserve units
    try:
        units = ds[varname].units
    except Exception as e:
        print(e)
        units = ""
    print("units:", units)

    ds_regridded[varname] = ds_regridded[varname].assign_attrs({"units": units})

    if debug:
        print("ds_regridded:", ds_regridded)
    return ds_regridded


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
