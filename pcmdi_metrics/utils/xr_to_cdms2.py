import numpy as np
import pandas as pd
import xarray as xr
from xarray.coding.times import CFDatetimeCoder, CFTimedeltaCoder


def encode(var):
    return CFTimedeltaCoder().encode(CFDatetimeCoder().encode(var.variable))


def xarray_to_cdms2(dataarray, copy=True):
    """
    Convert an xarray DataArray into a cdms2 variable.

    Parameters
    ----------
    dataarray : xarray.DataArray
        The input DataArray to be converted into a cdms2 variable.
    copy : bool, optional
        If True, the data is copied to the new cdms2 variable. Default is True.

    Returns
    -------
    cdms2_var : cdms2.variable.TransientVariable
        The resulting cdms2 variable containing the data and metadata from the input DataArray.

    Notes
    -----
    - This function does not require cdms2 as a hard dependency; it is imported within the function.
    - 1D axes are created for each dimension in the DataArray.
    - Attributes from the DataArray and its coordinates are transferred to the cdms2 variable and axes.
    - Handles curvilinear and unstructured grids by creating appropriate cdms2 axes and grids if present in the DataArray coordinates.
    - Missing values in the DataArray are masked in the resulting cdms2 variable.

    References
    ----------
    .. [1] xarray conversion utilities: https://github.com/pydata/xarray/blob/a45480f6f81851e4456f0ad0cab4e5e0d6bd70c2/xarray/convert.py#L90
    """

    # we don't want cdms2 to be a hard dependency
    import cdms2

    def set_cdms2_attrs(var, attrs):
        for k, v in attrs.items():
            setattr(var, k, v)

    # 1D axes
    axes = []
    for dim in dataarray.dims:
        coord = encode(dataarray.coords[dim])
        axis = cdms2.createAxis(coord.values, id=dim)
        set_cdms2_attrs(axis, coord.attrs)
        axes.append(axis)

    # Data
    var = encode(dataarray)
    cdms2_var = cdms2.createVariable(
        var.values, axes=axes, id=dataarray.name, mask=pd.isnull(var.values), copy=copy
    )

    # Attributes
    set_cdms2_attrs(cdms2_var, var.attrs)

    # Curvilinear and unstructured grids
    if dataarray.name not in dataarray.coords:
        cdms2_axes = {}
        for coord_name in set(dataarray.coords.keys()) - set(dataarray.dims):
            coord_array = dataarray.coords[coord_name].to_numpy()

            cdms2_axis_cls = (
                cdms2.coord.TransientAxis2D
                if coord_array.ndim
                else cdms2.auxcoord.TransientAuxAxis1D
            )
            cdms2_axis = cdms2_axis_cls(coord_array)
            if cdms2_axis.isLongitude():
                cdms2_axes["lon"] = cdms2_axis
            elif cdms2_axis.isLatitude():
                cdms2_axes["lat"] = cdms2_axis

        if "lon" in cdms2_axes and "lat" in cdms2_axes:
            if len(cdms2_axes["lon"].shape) == 2:
                cdms2_grid = cdms2.hgrid.TransientCurveGrid(
                    cdms2_axes["lat"], cdms2_axes["lon"]
                )
            else:
                cdms2_grid = cdms2.gengrid.AbstractGenericGrid(
                    cdms2_axes["lat"], cdms2_axes["lon"]
                )
            for axis in cdms2_grid.getAxisList():
                cdms2_var.setAxis(cdms2_var.getAxisIds().index(axis.id), axis)
            cdms2_var.setGrid(cdms2_grid)

    return cdms2_var


def cdms2_to_xarray(tv):
    """
    Convert a cdms2 TransientVariable to an xarray DataArray.

    Parameters:
    -----------
    tv : cdms2.tvariable.TransientVariable
        The cdms2 TransientVariable to convert.

    Returns:
    --------
    xr.DataArray
        The equivalent xarray DataArray.
    """
    import cdms2

    if not isinstance(tv, cdms2.tvariable.TransientVariable):
        raise TypeError("Input must be a cdms2 TransientVariable")

    # Extract data
    data = np.array(tv)

    # Extract dimension names
    dims = tv.getAxisIds()

    # Extract coordinates
    coords = {}
    for dim in dims:
        axis = tv.getAxis(tv.getAxisIndex(dim))
        coords[dim] = np.array(axis)

        # Include axis attributes as coordinate attributes
        if axis.attributes:
            coords[dim] = xr.DataArray(coords[dim], dims=(dim,), attrs=axis.attributes)

    # Variable attributes
    attrs = tv.attributes

    # Create the DataArray
    da = xr.DataArray(data, dims=dims, coords=coords, attrs=attrs, name=tv.id)

    return da
