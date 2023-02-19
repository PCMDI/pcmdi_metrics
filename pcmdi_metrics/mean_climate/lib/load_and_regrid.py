from pcmdi_metrics.io import xcdat_open
import cftime


def load_and_regrid(data_path, varname, level=None, t_grid=None, decode_times=True, regrid_tool='regrid2', debug=False):
    """Load data and regrid to target grid

    Args:
        data_path (str): full data path for nc or xml file
        varname (str): variable name
        level (float): level to extract (unit in hPa)
        t_grid (xarray.core.dataset.Dataset): target grid to regrid
        decode_times (bool): Default is True. decode_times=False will be removed once obs4MIP written using xcdat
        regrid_tool (str): Name of the regridding tool. See https://xcdat.readthedocs.io/en/stable/generated/xarray.Dataset.regridder.horizontal.html for more info
        debug (bool): Default is False. If True, print more info to help debugging process
    """
    # load data
    ds = xcdat_open(data_path, data_var=varname, decode_times=decode_times)  # NOTE: decode_times=False will be removed once obs4MIP written using xcdat
    # time bound check -- add proper time bound info if cdms-generated annual cycle is loaded
    if not isinstance(ds.time.values[0], cftime._cftime.DatetimeProlepticGregorian) and "units" not in list(ds.time.attrs.keys()):
        ds.time.attrs['units'] = "days since 0001-01-01"
        ds = xc.decode_time(ds)
    # level
    if level is not None:
        level = level * 100  # hPa to Pa
        ds = ds.sel(plev=level)
    if debug:
        print('ds:', ds)
    # regrid
    ds_regridded = ds.regridder.horizontal(varname, t_grid, tool=regrid_tool)
    if debug:
        print('ds_regridded:', ds_regridded)
    return ds_regridded
