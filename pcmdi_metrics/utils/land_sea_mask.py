import os
import sys
import time
import warnings
from typing import Union

import numpy as np
import numpy.ma as ma
import regionmask
import xarray as xr
import xcdat as xc

from pcmdi_metrics import resources
from pcmdi_metrics.io import get_grid


def create_land_sea_mask(
    obj: Union[xr.Dataset, xr.DataArray],
    lon_key: str = None,
    lat_key: str = None,
    as_boolean: bool = False,
    method: str = "regionmask",
) -> xr.DataArray:
    """Generate a land-sea mask (1 for land, 0 for sea) for a given xarray Dataset or DataArray.

    Parameters
    ----------
    obj : Union[xr.Dataset, xr.DataArray]
        The Dataset or DataArray object.
    lon_key : str, optional
        Name of DataArray for longitude, by default None
    lat_key : str, optional
        Name of DataArray for latitude, by default None
    as_boolean : bool, optional
        Set mask value to True (land) or False (ocean), by default False, thus 1 (land) and 0 (ocean).
    method : str, optional
        Method to use for creating the mask, either 'regionmask' or 'pcmdi', by default 'regionmask'.

    Returns
    -------
    xr.DataArray
        A DataArray of land-sea mask (1 or 0 for land or sea, or True or False for land or sea).

    Examples
    --------
    >>> from pcmdi_metrics.utils import create_land_sea_mask  # import function
    >>> mask = create_land_sea_mask(ds)  #  Generate land-sea mask (land: 1, sea: 0)
    >>> mask = create_land_sea_mask(ds, as_boolean=True)  # Generate land-sea mask (land: True, sea: False)
    >>> mask = create_land_sea_mask(ds, method="pcmdi")  # Use PCMDI method
    """

    # Create a land-sea mask
    if method.lower() == "regionmask":
        # Use regionmask
        land_mask = regionmask.defined_regions.natural_earth_v5_0_0.land_110

        # Get the longitude and latitude from the xarray dataset
        if lon_key is None:
            lon_key = xc.axis.get_dim_keys(obj, axis="X")
        if lat_key is None:
            lat_key = xc.axis.get_dim_keys(obj, axis="Y")

        lon = obj[lon_key]
        lat = obj[lat_key]

        # Mask the land-sea mask to match the dataset's coordinates
        land_sea_mask = land_mask.mask(lon, lat=lat)

        if as_boolean:
            # Convert the 0 (land) & nan (ocean) land-sea mask to a boolean mask
            land_sea_mask = xr.where(land_sea_mask, False, True)
        else:
            # Convert the boolean land-sea mask to a 1/0 mask
            land_sea_mask = xr.where(land_sea_mask, 0, 1)

    elif method.lower() == "pcmdi":
        # Use the PCMDI method developed by Taylor and Doutriaux (2000)
        land_sea_mask = generate_land_sea_mask__pcmdi(obj)

        if as_boolean:
            # Convert the 1/0 land-sea mask to a boolean mask
            land_sea_mask = land_sea_mask.astype(bool)

    else:
        raise ValueError("Unknown method '%s'. Please choose 'regionmask' or 'pcmdi'")

    return land_sea_mask


def find_max(da: xr.DataArray) -> float:
    """Find the maximum value in a given xarray DataArray.

    Parameters
    ----------
    da : xr.DataArray
        Input DataArray.

    Returns
    -------
    float
        Maximum value in the DataArray.
    """
    return float(da.max())


def find_min(da: xr.DataArray) -> float:
    """Find the minimum value in a given xarray DataArray.

    Parameters
    ----------
    da : xr.DataArray
        Input DataArray.

    Returns
    -------
    float
        Minimum value in the DataArray.
    """
    return float(da.min())


def apply_landmask(
    obj: Union[xr.Dataset, xr.DataArray],
    data_var: str = None,
    landfrac: xr.DataArray = None,
    keep_over: str = "ocean",
    land_criteria: float = 0.8,
    ocean_criteria: float = 0.2,
) -> xr.DataArray:
    """Apply a land-sea mask to a given DataArray in an xarray Dataset.

    Parameters
    ----------
    obj : Union[xr.Dataset, xr.DataArray]
        The Dataset or DataArray object to apply a land-sea mask.
    data_var : str
        Name of DataArray in the Dataset, required if obs is an Dataset.
    landfrac : xr.DataArray
        Data array for land fraction that consists of 0 for ocean and 1 for land (fraction for grid along coastline), by default None.
        If None, it is going to be created.
    keep_over : str
        Specify whether to keep values "land" or "ocean".
    land_criteria : float, optional
        When the fraction is equal to land_criteria or larger, the grid will be considered as land, by default 0.8.
    ocean_criteria : float, optional
        When the fraction is equal to ocean_criteria or smaller, the grid will be considered as ocean, by default 0.2.

    Returns
    -------
    xr.DataArray
        Land-sea mask applied DataArray.

    Examples
    --------
    >>> from pcmdi_metrics.utils import apply_landmask
    >>> # To keep values over land only (mask over ocean)
    >>> da_land = apply_landmask(da, landfrac=mask, keep_over="land")  # use DataArray
    >>> da_land = apply_landmask(ds, data_var="ts", landfrac=mask, keep_over="land")  # use DataSet
    >>> # To Keep values over ocean only (mask over land):
    >>> da_ocean = apply_landmask(da, landfrac=mask, keep_over="ocean")  # use DataArray
    >>> da_ocean = apply_landmask(ds, data_var="ts", landfrac=mask, keep_over="ocean")  # use DataSet
    """

    if isinstance(obj, xr.DataArray):
        data_array = obj.copy()
    elif isinstance(obj, xr.Dataset):
        if data_var is None:
            raise ValueError("Invalid value for data_var. Provide name of DataArray.")
        else:
            data_array = obj[data_var].copy()

    # Validate landfrac
    generateLandSeaMask = False
    where_method = "xarray"
    if landfrac is None:
        generateLandSeaMask = True
    else:
        data_grid = get_grid(data_array)
        lf_grid = get_grid(landfrac)

        if data_grid.identical(lf_grid):
            pass
        else:
            if data_grid.equals(lf_grid):
                pass
            else:
                if data_grid.sizes == lf_grid.sizes:
                    where_method = "numpy"

    if generateLandSeaMask:
        landfrac = create_land_sea_mask(data_array)
        warnings.warn(
            "landfrac is not provided thus generated using the 'create_land_sea_mask' function"
        )

    # Check units of landfrac
    percentage = False
    if find_min(landfrac) == 0 and find_max(landfrac) == 100:
        percentage = True
    if "units" in list(landfrac.attrs.keys()):
        if landfrac.units == "%":
            percentage = True

    # Convert landfrac to a fraction if it's in percentage form
    if percentage:
        landfrac = landfrac.copy() / 100.0

    # Validate keep_over parameter
    if keep_over not in ["land", "ocean"]:
        raise ValueError(
            "Invalid value for keep_over. Choose either 'land' or 'ocean'."
        )

    # Apply land and ocean masks
    if where_method == "xarray":
        if keep_over == "land":
            data_array = data_array.where(landfrac >= land_criteria)
        elif keep_over == "ocean":
            data_array = data_array.where(landfrac <= ocean_criteria)

    elif where_method == "numpy":
        # Expand data1 to match the shape of landfrac along the time dimension
        expanded_landfrac = np.expand_dims(landfrac.data, axis=0)
        expanded_landfrac = np.repeat(
            expanded_landfrac, data_array.shape[0], axis=0
        )  # Repeat along the time dimension

        # Mask data based on landfrac
        if keep_over == "land":
            data_array.data = ma.masked_where(
                expanded_landfrac < land_criteria, data_array.data
            )
        elif keep_over == "ocean":
            data_array.data = ma.masked_where(
                expanded_landfrac > ocean_criteria, data_array.data
            )

    return data_array


def apply_oceanmask(
    obj: Union[xr.Dataset, xr.DataArray],
    data_var: str = None,
    landfrac: xr.DataArray = None,
    land_criteria: float = 0.8,
    ocean_criteria: float = 0.2,
) -> xr.DataArray:
    masked_data_array = apply_landmask(
        obj,
        data_var=data_var,
        landfrac=landfrac,
        keep_over="land",
        land_criteria=land_criteria,
        ocean_criteria=ocean_criteria,
    )
    return masked_data_array


def generate_land_sea_mask__pcmdi(
    target_grid,
    source=None,
    data_var="sftlf",
    maskname="lsmask",
    regridTool="regrid2",
    threshold_1=0.2,
    threshold_2=0.3,
    debug=False,
):
    """Generates a best guess mask on any rectilinear grid, using the method described in `PCMDI's report #58`_

    Parameters
    ----------
    target_grid : xarray.Dataset
        Either a xcdat/xarray Dataset with a grid, or a xcdat grid (rectilinear grid only)
    source : xarray.Dataset, optional
        A xcdat/xarray Dataset that contains a DataArray of a fractional (0.0 to 1.0) land sea mask,
        where 1 means all land., by default None
    data_var : str, optional
        name of DataArray for land sea fraction/mask variable in `source`, by default "sftlf"
    maskname : str, optional
        Variable name for returning DataArray, by default "lsmask"
    regridTool : str, optional
        Which xcdat regridder tool to use, by default "regrid2"
    threshold_1 : float, optional
        Criteria for detecting cells with possible increment see report for detail difference threshold, by default 0.2
    threshold_2 : float, optional
        Criteria for detecting cells with possible increment see report for detail water/land content threshold, by default 0.3
    debug : bool, optional
        Switch to print more interim outputs to help debugging, by default False

    Returns
    -------
    xarray.DataArray
        landsea mask on target grid (1: land, 0: water).

    Raises
    ------
    ValueError
        _description_

    References
    ----------
    .. _PCMDI's report #58: https://pcmdi.llnl.gov/report/ab58.html

    History
    -------
    2023-06 The [original code](https://github.com/CDAT/cdutil/blob/master/cdutil/create_landsea_mask.py) was rewritten using xarray and xcdat by Jiwoo Lee
    """

    if source is None:
        egg_pth = resources.resource_path()
        source_path = os.path.join(egg_pth, "navy_land.nc")
        if not os.path.isfile(source_path):
            # pip install process places data files in different place, so checking here as well
            source_path = os.path.join(
                sys.prefix, "share/pcmdi_metrics", "navy_land.nc"
            )
        ds = xc.open_dataset(source_path, decode_times=False).load()
    else:
        ds = source.copy()
        if not isinstance(ds, xr.Dataset):
            raise ValueError(
                "ERROR: type of source, ",
                type(source),
                " is not acceptable. It should be <xarray.Dataset>",
            )

    # Regrid
    if target_grid.equals(ds):
        ds_regrid = ds.copy()  # testing purpose
    else:
        start_time_r = time.time()
        ds_regrid = ds.regridder.horizontal(data_var, target_grid, tool=regridTool)
        end_time_r = time.time()

        if debug:
            print(
                "Elapsed time (regridder.horizontal):",
                end_time_r - start_time_r,
                "seconds",
            )

        # Add missed information during the regrid process
        # (this might be a bug... will report it to xcdat team later)
        if "axis" not in ds_regrid[data_var].lat.attrs.keys():
            ds_regrid[data_var].lat.attrs["axis"] = "Y"
        if "axis" not in ds_regrid[data_var].lon.attrs.keys():
            ds_regrid[data_var].lon.attrs["axis"] = "X"
        if "bounds" not in ds_regrid[data_var].lat.attrs.keys():
            ds_regrid[data_var].lat.attrs["bounds"] = "lat_bnds"
        if "bounds" not in ds_regrid[data_var].lon.attrs.keys():
            ds_regrid[data_var].lon.attrs["bounds"] = "lon_bnds"
        if "units" not in ds_regrid[data_var].lat.attrs:
            ds_regrid[data_var].lat.attrs["units"] = "degrees_north"

    # re-generate lat lon bounds (original bounds are 2d arrays where 1d array for each is expected)
    ds_regrid = (
        ds_regrid.drop_vars(
            [
                ds_regrid[data_var].lat.attrs["bounds"],
                ds_regrid[data_var].lon.attrs["bounds"],
            ]
        )
        .bounds.add_bounds("Y")
        .bounds.add_bounds("X")
    )

    # First guess, anything greater than 50% is land to ignore rivers and lakes
    mask = xr.where(ds_regrid[data_var] > 0.5, 1, 0)

    if debug:
        ds_regrid[data_var + "_regrid"] = ds_regrid[data_var].copy()
        ds_regrid[data_var + "_firstGuess"] = mask

    # Improve
    UL, UC, UR, ML, MR, LL, LC, LR = _create_surrounds(
        ds_regrid, data_var=data_var, debug=debug
    )

    cont = True
    i = 0

    while cont:
        mask_improved = _improve(
            mask,
            ds_regrid,
            UL,
            UC,
            UR,
            ML,
            MR,
            LL,
            LC,
            LR,
            data_var=data_var,
            threshold_1=threshold_1,
            threshold_2=threshold_2,
            regridTool=regridTool,
            debug=debug,
        )

        if mask_improved.equals(mask) or i > 25:
            cont = False

        mask = mask_improved.astype("i")

        if debug:
            print("test i:", i)

        i += 1

    mask = mask.rename(maskname)

    # Reverse the values (0 to 1 and 1 to 0)
    # mask = xr.where(mask == 0, 1, 0)

    return mask


def _create_surrounds(ds, data_var="sftlf", debug=False):
    start_time = time.time()
    data = ds[data_var].data
    sh = list(data.shape)
    L = ds["lon"]
    bL = ds[ds.lon.attrs["bounds"]].data

    L_isCircular = _isCircular(L)
    L_modulo = 360

    if _isCircular(L) and bL[-1][1] - bL[0][0] % L_modulo == 0:
        sh[0] = sh[0] - 2
    else:
        sh[0] = sh[0] - 2
        sh[1] = sh[1] - 2

    UL = np.ones(sh)
    UC = np.ones(sh)
    UR = np.ones(sh)
    ML = np.ones(sh)
    MR = np.ones(sh)
    LL = np.ones(sh)
    LC = np.ones(sh)
    LR = np.ones(sh)

    if L_isCircular and bL[-1][1] - bL[0][0] % L_modulo == 0:
        UC[:, :] = data[2:]
        LC[:, :] = data[:-2]
        ML[:, 1:] = data[1:-1, :-1]
        ML[:, 0] = data[1:-1, -1]
        MR[:, :-1] = data[1:-1, 1:]
        MR[:, -1] = data[1:-1, 0]
        UL[:, 1:] = data[2:, :-1]
        UL[:, 0] = data[2:, -1]
        UR[:, :-1] = data[2:, 1:]
        UR[:, -1] = data[2:, 0]
        LL[:, 1:] = data[:-2, :-1]
        LL[:, 0] = data[:-2, -1]
        LR[:, :-1] = data[:-2, 1:]
        LR[:, -1] = data[:-2, 0]
    else:
        UC[:, :] = data[2:, 1:-1]
        LC[:, :] = data[:-2, 1:-1]
        ML[:, :] = data[1:-1, :-2]
        MR[:, :] = data[1:-1, 2:]
        UL[:, :] = data[2:, :-2]
        UR[:, :] = data[2:, 2:]
        LL[:, :] = data[:-2, :-2]
        LR[:, :] = data[:-2, 2:]

    end_time = time.time()
    if debug:
        elapsed_time = end_time - start_time
        print("Elapsed time (_create_surrounds):", elapsed_time, "seconds")

    return UL, UC, UR, ML, MR, LL, LC, LR


def _isCircular(lons):
    baxis = lons[0]  # beginning of axis
    eaxis = lons[-1]  # end of axis
    deltaend = lons[-1] - lons[-2]  # delta between two end points
    eaxistest = eaxis + deltaend - baxis  # test end axis
    tol = 0.01 * deltaend
    if abs(eaxistest - 360) < tol:
        return True
    else:
        return False


def _improve(
    mask,
    ds_regrid,
    UL,
    UC,
    UR,
    ML,
    MR,
    LL,
    LC,
    LR,
    data_var="sftlf",
    threshold_1=0.2,
    threshold_2=0.3,
    regridTool="regrid2",
    debug=False,
):
    start_time = time.time()

    ds_mask_approx = _map2four(
        mask, ds_regrid, data_var=data_var, regridTool=regridTool, debug=debug
    )
    diff = ds_regrid[data_var] - ds_mask_approx[data_var]

    # Land point conversion
    c1 = np.greater(diff, threshold_1)  # xr.DataArray
    c2 = np.greater(ds_regrid[data_var], threshold_2)  # xr.DataArray
    c = np.logical_and(c1, c2)
    ds_regrid["c"] = c

    # Now figures out local maxima
    cUL, cUC, cUR, cML, cMR, cLL, cLC, cLR = _create_surrounds(ds_regrid, data_var="c")

    L = ds_regrid["lon"]
    bL = ds_regrid[ds_regrid.lon.attrs["bounds"]].data

    L_modulo = 360
    L_isCircular = _isCircular(L)

    if L_isCircular and bL[-1][1] - bL[0][0] % L_modulo == 0:
        c = c[1:-1]  # elimnitates north and south poles
        tmp = ds_regrid[data_var].data[1:-1]
    else:
        c = c[1:-1, 1:-1]  # elimnitates north and south poles
        tmp = ds_regrid[data_var].data[1:-1, 1:-1]
    m = np.logical_and(c, np.greater(tmp, np.where(cUL, UL, 0.0)))
    m = np.logical_and(m, np.greater(tmp, np.where(cUC, UC, 0.0)))
    m = np.logical_and(m, np.greater(tmp, np.where(cUR, UR, 0.0)))
    m = np.logical_and(m, np.greater(tmp, np.where(cML, ML, 0.0)))
    m = np.logical_and(m, np.greater(tmp, np.where(cMR, MR, 0.0)))
    m = np.logical_and(m, np.greater(tmp, np.where(cLL, LL, 0.0)))
    m = np.logical_and(m, np.greater(tmp, np.where(cLC, LC, 0.0)))
    m = np.logical_and(m, np.greater(tmp, np.where(cLR, LR, 0.0)))
    # Ok now update the mask by setting these points to land
    mask2 = mask * 1.0
    if _isCircular(L) and bL[-1][1] - bL[0][0] % L_modulo == 0:
        mask2[1:-1] = xr.where(m, 1, mask[1:-1])
    else:
        mask2[1:-1, 1:-1] = xr.where(m, 1, mask[1:-1, 1:-1])

    # ocean point conversion
    c1 = np.less(diff, -threshold_1)
    c2 = np.less(ds_regrid[data_var], 1.0 - threshold_2)
    c = np.logical_and(c1, c2)
    ds_regrid["c"] = c

    cUL, cUC, cUR, cML, cMR, cLL, cLC, cLR = _create_surrounds(ds_regrid, data_var="c")

    if L_isCircular and bL[-1][1] - bL[0][0] % L_modulo == 0:
        c = c[1:-1]  # elimnitates north and south poles
        tmp = ds_regrid[data_var].data[1:-1]
    else:
        c = c[1:-1, 1:-1]  # elimnitates north and south poles
        tmp = ds_regrid[data_var].data[1:-1, 1:-1]
    # Now figures out local maxima
    m = np.logical_and(c, np.less(tmp, np.where(cUL, UL, 1.0)))
    m = np.logical_and(m, np.less(tmp, np.where(cUC, UC, 1.0)))
    m = np.logical_and(m, np.less(tmp, np.where(cUR, UR, 1.0)))
    m = np.logical_and(m, np.less(tmp, np.where(cML, ML, 1.0)))
    m = np.logical_and(m, np.less(tmp, np.where(cMR, MR, 1.0)))
    m = np.logical_and(m, np.less(tmp, np.where(cLL, LL, 1.0)))
    m = np.logical_and(m, np.less(tmp, np.where(cLC, LC, 1.0)))
    m = np.logical_and(m, np.less(tmp, np.where(cLR, LR, 1.0)))
    # Ok now update the mask by setting these points to ocean
    if L_isCircular and bL[-1][1] - bL[0][0] % L_modulo == 0:
        mask2[1:-1] = xr.where(m, 0, mask2[1:-1])
    else:
        mask2[1:-1, 1:-1] = xr.where(m, 0, mask2[1:-1, 1:-1])

    end_time = time.time()
    if debug:
        elapsed_time = end_time - start_time
        print("Elapsed time (_improve):", elapsed_time, "seconds")

    return mask2


def _map2four(mask, ds_regrid, data_var="sftlf", regridTool="regrid2", debug=False):
    if debug:
        print("mask.shape:", mask.shape)
        print("ds_regrid[data_var].shape:", ds_regrid[data_var].shape)

    ds_tmp = ds_regrid.copy()
    ds_tmp[data_var] = mask

    start_time_c = time.time()

    lons = ds_regrid.lon.data
    lats = ds_regrid.lat.data
    lonso = lons[::2]
    lonse = lons[1::2]
    latso = lats[::2]
    latse = lats[1::2]

    lat_delta = (lats[-1] - lats[0]) / len(lats) * 2
    lon_delta = (lons[-1] - lons[0]) / len(lons) * 2

    oo = xc.create_uniform_grid(
        latso[0], latso[-1], lat_delta, lonso[0], lonso[-1], lon_delta
    )
    oe = xc.create_uniform_grid(
        latso[0], latso[-1], lat_delta, lonse[0], lonse[-1], lon_delta
    )
    eo = xc.create_uniform_grid(
        latse[0], latse[-1], lat_delta, lonso[0], lonso[-1], lon_delta
    )
    ee = xc.create_uniform_grid(
        latse[0], latse[-1], lat_delta, lonse[0], lonse[-1], lon_delta
    )

    end_time_c = time.time()

    doo = ds_tmp.regridder.horizontal(data_var, oo, tool=regridTool)
    doe = ds_tmp.regridder.horizontal(data_var, oe, tool=regridTool)
    deo = ds_tmp.regridder.horizontal(data_var, eo, tool=regridTool)
    dee = ds_tmp.regridder.horizontal(data_var, ee, tool=regridTool)

    end_time_r = time.time()

    out = np.zeros(mask.shape, dtype="f")

    if debug:
        print("out.shape:", out.shape)
        print("doo.shape:", doo[data_var].data.shape)
        print("doe.shape:", doe[data_var].data.shape)
        print("deo.shape:", deo[data_var].data.shape)
        print("dee.shape:", dee[data_var].data.shape)

    out[::2, ::2] = doo[data_var].data
    out[::2, 1::2] = doe[data_var].data
    out[1::2, ::2] = deo[data_var].data
    out[1::2, 1::2] = dee[data_var].data

    ds_out = ds_regrid.copy()
    ds_out[data_var] = (("lat", "lon"), out)

    end_time_o = time.time()

    end_time = time.time()

    if debug:
        elapsed_time = end_time - start_time_c
        print("Elapsed time (_map2four):", elapsed_time, "seconds")
        print(
            "Elapsed time (_map2four, create_uniform_grid):",
            end_time_c - start_time_c,
            "seconds",
        )
        print(
            "Elapsed time (_map2four, regridder.horizontal):",
            end_time_r - end_time_c,
            "seconds",
        )
        print("Elapsed time (_map2four, out):", end_time_o - end_time_r, "seconds")

    return ds_out
