import xarray as xr
import xcdat as xc


def create_target_grid(target_grid_resolution: str) -> xr.Dataset:
    """Generate a global uniform grid for given resolution

    Parameters
    ----------
    target_grid_resolution : str
        grid resolution in degree for lat and lon. e.g., "2.5x2.5"

    Returns
    -------
    xr.Dataset
        generated grid
    """

    res = target_grid_resolution.split("x")
    lat_res = float(res[0])
    lon_res = float(res[1])
    start_lat = -90.0 + lat_res / 2
    start_lon = 0.0 + lon_res / 2
    end_lat = 90.0 - lat_res / 2
    end_lon = 360.0 - lon_res / 2

    t_grid = xc.create_uniform_grid(
        start_lat, end_lat, lat_res, start_lon, end_lon, lon_res
    )
    return t_grid
