import xarray as xr
import xcdat as xc


def create_target_grid(
    lat1: float = -90.0,
    lat2: float = 90.0,
    lon1: float = 0.0,
    lon2: float = 360.0,
    target_grid_resolution: str = "2.5x2.5",
) -> xr.Dataset:
    """Generate a uniform grid for given latitude/longitude ranges and resolution

    Parameters
    ----------
    lat1 : float, optional
        Starting latitude, by default -90.
    lat2 : float, optional
        Starting latitude, by default 90.
    lon1 : float, optional
        Starting latitude, by default 0.
    lon2 : float, optional
        Starting latitude, by default 360.
    target_grid_resolution : str, optional
        grid resolution in degree for lat and lon, by default "2.5x2.5"

    Returns
    -------
    xr.Dataset
        generated grid

    Examples
    ---------
    Import:

    >>> from pcmdi_metrics.utils import create_target_grid

    Global uniform grid:

    >>> t_grid = create_target_grid(-90, 90, 0, 360, target_grid="5x5")

    Regional uniform grid:

    >>> t_grid = create_target_grid(30, 50, 100, 150, target_grid="0.5x0.5")
    """
    # generate target grid
    res = target_grid_resolution.split("x")
    lat_res = float(res[0])
    lon_res = float(res[1])
    start_lat = lat1 + lat_res / 2.0
    start_lon = lon1 + lon_res / 2.0
    end_lat = lat2 - lat_res / 2
    end_lon = lon2 - lon_res / 2
    t_grid = xc.create_uniform_grid(
        start_lat, end_lat, lat_res, start_lon, end_lon, lon_res
    )
    return t_grid
