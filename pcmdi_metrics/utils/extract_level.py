import xarray as xr
import numpy as np


def extract_level(
    data: xr.DataArray,
    level: float,
    lev_dim: str = "plev",
    tolerance_pct: float = 0.1,
    debug: bool = False,
):
    """
    Extract a specific pressure level from data, handling floating-point precision issues.

    This function robustly extracts a pressure level from xarray data by first attempting
    exact selection, then falling back to nearest-neighbor selection if the exact value
    doesn't exist due to floating-point precision issues. It validates that the nearest
    level is within an acceptable tolerance.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Input data with pressure level coordinate.
    level : float
        Target pressure level in hPa.
    lev_dim : str, optional
        Name of the pressure level dimension. Default is "plev".
    tolerance_pct : float, optional
        Maximum acceptable percentage difference between requested and actual level.
        Default is 0.1%.
    debug : bool, optional
        If True, print diagnostic information. Default is False.

    Returns
    -------
    xr.DataArray or xr.Dataset
        Data extracted at the specified pressure level.

    Raises
    ------
    ValueError
        If lev_dim is not in coordinates, or if nearest level exceeds tolerance.

    Examples
    --------
    >>> psi_500 = _extract_level(psi, 500, lev_dim="plev")
    """

    def find_nearest(array, value):
        """Find the nearest value in array to the target value."""
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]

    # Validate inputs
    if level is None:
        return data

    level = float(level)

    # Check if level dimension exists
    if lev_dim not in data.coords:
        raise ValueError(
            f"ERROR: {lev_dim} is not in the data coordinates.\n"
            f"Available coordinates: {list(data.coords.keys())}"
        )

    # Determine units and convert level to match data units
    lev_units = data[lev_dim].attrs.get("units", "Pa")
    if lev_units == "Pa" or np.max(data[lev_dim].values) > 10000:
        level_in_data_units = level * 100  # Convert hPa to Pa
        units_str = "Pa"
    else:
        level_in_data_units = level  # Already in hPa
        units_str = "hPa"

    if debug:
        print(f"Extracting level: {level} hPa ({level_in_data_units} {units_str})")
        print(f"Available levels: {data[lev_dim].values}")

    # Try exact selection first
    try:
        result = data.sel({lev_dim: level_in_data_units})
        if debug:
            print("Exact level found")
        return result
    except (KeyError, ValueError) as ex:
        # Exact level not found, use nearest neighbor
        if debug:
            print(f"Exact level not found: {ex}")

        nearest_level = find_nearest(data[lev_dim].values, level_in_data_units)

        diff_percentage = (
            abs(nearest_level - level_in_data_units) / level_in_data_units * 100
        )

        if debug or diff_percentage > 0.01:  # Always warn if difference > 0.01%
            print(f"WARNING: Exact level {level_in_data_units} {units_str} not found")
            print(f"  Requested level: {level_in_data_units} {units_str}")
            print(f"  Nearest level:   {nearest_level} {units_str}")
            print(f"  Difference:      {diff_percentage:.4f}%")

        if diff_percentage < tolerance_pct:
            result = data.sel({lev_dim: level_in_data_units}, method="nearest")
            if debug:
                print("  Difference is within acceptable tolerance")
            return result
        else:
            raise ValueError(
                f"ERROR: Nearest level differs by {diff_percentage:.4f}%, "
                f"exceeding tolerance of {tolerance_pct}%.\n"
                f"Requested: {level_in_data_units} {units_str}, "
                f"Nearest: {nearest_level} {units_str}"
            )

    return result