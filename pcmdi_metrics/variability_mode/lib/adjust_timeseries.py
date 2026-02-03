import copy
import xarray as xr

from pcmdi_metrics.io import (
    get_latitude_bounds,
    get_latitude_bounds_key,
    get_longitude_bounds,
    get_longitude_bounds_key,
    get_time_key,
    region_subset,
    select_subset,
)
from pcmdi_metrics.utils import custom_season_departure


def adjust_timeseries(
    ds: xr.Dataset,
    data_var: str,
    mode: str,
    season: str,
    regions_specs: dict = None,
    RmDomainMean: bool = True,
) -> xr.Dataset:
    """
    Remove annual cycle (for all modes) and get its seasonal mean time series if
    needed. Then calculate residual by subtraction domain (or global) average.
    Input
    - ds: array (t, y, x)
    Output
    - timeseries_season: array (t, y, x)
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError(
            "The first parameter of adjust_timeseries must be an xarray Dataset"
        )
    # Reomove annual cycle (for all modes) and get its seasonal mean time series if needed
    ds_anomaly = get_anomaly_timeseries(ds, data_var, season)
    # Calculate residual by subtracting domain (or global) average
    ds_residual = get_residual_timeseries(
        ds_anomaly, data_var, mode, regions_specs, RmDomainMean=RmDomainMean
    )
    # return result
    return ds_residual.bounds.add_missing_bounds()


def get_anomaly_timeseries(ds: xr.Dataset, data_var: str, season: str) -> xr.Dataset:
    """
    Get anomaly time series by removing annual cycle
    Input
    - timeseries: variable
    - season: string
    Output
    - timeseries_ano: variable
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError(
            "The first parameter of get_anomaly_timeseries must be an xarray Dataset"
        )
    # Get anomaly field by removing annual cycle
    ds_anomaly = ds.temporal.departures(data_var, freq="month", weighted=True)
    # Get temporal average if needed
    if season == "yearly":
        # yearly time series
        ds_anomaly = ds_anomaly.temporal.group_average(
            data_var, freq="year", weighted=True
        )
        # restore bounds (especially time bounds)
        ds_anomaly = ds_anomaly.bounds.add_missing_bounds()
        # get overall average
        ds_ave = ds_anomaly.temporal.average(data_var)
        # anomaly
        ds_anomaly[data_var] = ds_anomaly[data_var] - ds_ave[data_var]
    elif season == "monthly":
        pass
    elif season.upper() in ["DJF", "MAM", "JJA", "SON"]:
        ds_anomaly_all_seasons = ds_anomaly.temporal.departures(
            data_var,
            freq="season",
            weighted=True,
            season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},
        )
        ds_anomaly = select_by_season(ds_anomaly_all_seasons, season)
    else:
        try:
            ds_anomaly = custom_season_departure(ds_anomaly, data_var, season)
        except ValueError as e:
            print(f"Error: season code {season} is not recognized")
            raise e
    # return result
    return ds_anomaly


def select_by_season(ds: xr.Dataset, season: str) -> xr.Dataset:
    time_key = get_time_key(ds)
    ds_subset = ds.where(ds[time_key].dt.season == season, drop=True)
    # Preserve original spatial bounds info
    # Extract original bounds
    lat_bnds_key = get_latitude_bounds_key(ds)
    lon_bnds_key = get_longitude_bounds_key(ds)
    # Assign back to the new dataset
    ds_subset[lat_bnds_key] = get_latitude_bounds(ds)
    ds_subset[lon_bnds_key] = get_longitude_bounds(ds)
    return ds_subset


def get_residual_timeseries(
    ds_anomaly: xr.Dataset,
    data_var: str,
    mode: str,
    regions_specs: dict = None,
    RmDomainMean: bool = True,
) -> xr.Dataset:
    """
    Calculate residual by subtracting domain average (or global mean)
    Input
    - ds_anomaly: anomaly time series, array, 3d (t, y, x)
    - mode: string, mode name, must be defined in regions_specs
    - RmDomainMean: bool (True or False).
          If True, remove domain mean of each time step.
          Ref:
              Bonfils and Santer (2011)
                  https://doi.org/10.1007/s00382-010-0920-1
              Bonfils et al. (2015)
                  https://doi.org/10.1175/JCLI-D-15-0341.1
          If False, remove global mean of each time step for PDO, or
              do nothing for other modes
          Default is True for this function.
    - region_subdomain: lat lon range of sub domain for given mode, which was
          extracted from regions_specs -- that is a dict contains domain
          lat lon ragne for given mode
    Output
    - ds_residual: array, 3d (t, y, x)
    """
    if not isinstance(ds_anomaly, xr.Dataset):
        raise TypeError(
            "The first parameter of get_residual_timeseries must be an xarray Dataset"
        )
    ds_residual = copy.deepcopy(ds_anomaly)
    if RmDomainMean:
        # Get domain mean
        ds_anomaly_region = region_subset(
            ds_anomaly, mode, data_var=data_var, regions_specs=regions_specs
        )
        ds_anomaly_mean = ds_anomaly_region.spatial.average(data_var)
        # Subtract domain mean
        ds_residual[data_var] = ds_anomaly[data_var] - ds_anomaly_mean[data_var]
    else:
        if mode in ["PDO", "NPGO", "AMO"]:
            # Get global mean (latitude -60 to 70)
            ds_anomaly_subset = select_subset(ds_anomaly, lat=(-60, 70))
            ds_anomaly_subset_mean = ds_anomaly_subset.spatial.average(data_var)
            # Subtract global mean
            ds_residual[data_var] = (
                ds_anomaly[data_var] - ds_anomaly_subset_mean[data_var]
            )
    # return result
    return ds_residual
