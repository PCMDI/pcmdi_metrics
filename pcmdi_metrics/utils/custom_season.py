from typing import Union

import xarray as xr

from pcmdi_metrics.io import get_time_key


def generate_calendar_months(custom_season, output_type: str = "month_abbreviations"):
    """
    Generates a list of calendar months corresponding to the given custom season.

    Args:
        custom_season (str): A string representing a custom season (e.g., "MJJ").
        output_type (str, optional): default is "month_abbreviations" which returns month abbreviations. If set to "month_numbers", it will return months in numbers.

    Returns:
        list: A list of strings of calendar months corresponding to the given custom season, or a list of numbers

    Raises:
        ValueError: If the length of the custom season is longer than 12 or if the custom season is not found in the months.
        ValueError: If  `output_type` is not one of "month_abbreviations" or "month_numbers"

    Example:
        >>> generate_calendar_months("MJJ")
        ['May', 'Jun', 'Jul']
        >>> generate_calendar_months("MJJ", output_type="month_numbers")
        [5, 6, 7]
    """
    # Define the mapping of month abbreviations to full month names
    months_mapping = [
        ("J", "Jan", 1),
        ("F", "Feb", 2),
        ("M", "Mar", 3),
        ("A", "Apr", 4),
        ("M", "May", 5),
        ("J", "Jun", 6),
        ("J", "Jul", 7),
        ("A", "Aug", 8),
        ("S", "Sep", 9),
        ("O", "Oct", 10),
        ("N", "Nov", 11),
        ("D", "Dec", 12),
    ] * 2  # Repeat the mapping to cover cases where the custom season wraps around to the beginning of the year

    # Generate a string representation of all months by concatenating their abbreviations
    months = "".join([m[0] for m in months_mapping])

    # Sanity check
    custom_season = custom_season.upper()

    # Check if the length of the custom season exceeds 12
    if len(custom_season) > 12:
        raise ValueError("Custom season length cannot be longer than 12")

    if output_type == "month_abbreviations":
        k = 1
    elif output_type == "month_numbers":
        k = 2
    else:
        raise ValueError(
            f"{output_type} should be either of 'month_abbreviations' or 'numbers'"
        )

    # Iterate through the months to find the starting index of the custom season
    for i in range(len(months) - len(custom_season) + 1):
        if months[i : i + len(custom_season)] == custom_season:
            # Once the custom season is found, return the corresponding list of months
            return [months_mapping[(i + j) % 12][k] for j in range(len(custom_season))]

    # If the custom season is not found, raise a ValueError
    raise ValueError(f"Custom season {custom_season} not found in months {months}")


def subset_timesteps_in_custom_season(
    ds: Union[xr.Dataset, xr.DataArray], season: str
) -> Union[xr.Dataset, xr.DataArray]:
    """Subset an xarray Dataset/DataArray to contain only timesteps within a specified custom season.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        Input xarray Dataset/DataArray
    season : str
        A string representing a custom season (e.g., "MJJ"). Must consist of one or more month abbreviations.

    Returns
    -------
    Union[xr.Dataset, xr.DataArray]
        xarray Dataset/DataArray subsetted to contain only timesteps within the specified custom season.
    """
    months = generate_calendar_months(season, output_type="month_numbers")
    time_key = get_time_key(ds)
    ds_subset = ds.sel(time=ds[f"{time_key}.month"].isin(months))

    return ds_subset


def custom_season_average(
    ds: xr.Dataset, data_var: str, season: str, method: str = "xcdat"
) -> xr.Dataset:
    """Calculates the average of a user defined season in each year.

    Parameters
    ----------
    ds : xr.Dataset
        Input xarray Dataset
    data_var : str
        name of variable (dataArray)
    season : str
        A string representing a custom season (e.g., "MJJ"). Must consist of one or more month abbreviations.
    method : str, optional
        method for yearly average, by default "xcdat", optional alternative is "xcdat"

    Raises
    ------
        ValueError: If  `method` is not one of "xcdat" or "xarray"

    Returns
    -------
    xr.Dataset
        xarray Dataset that contains timeseries of seasonal mean for each year
    """
    ds_subset = subset_timesteps_in_custom_season(ds, season.upper())
    if method == "xcdat":
        # use xcdat group average that considers weighting
        yearly_means = ds_subset.temporal.group_average(data_var, "year")
    elif method == "xarray":
        # use xarray group average that does not consider weighting
        time_key = get_time_key(ds)
        yearly_means = ds_subset.groupby(f"{time_key}.year").mean(dim=time_key)
    else:
        raise ValueError(
            f"{method} is not defined. It should be either of ['xcdat', 'xarray']"
        )

    return yearly_means


def custom_season_departure(
    ds: xr.Dataset, data_var: str, season: str, method: str = "xcdat"
) -> xr.Dataset:
    """Calculate the departure from a reference seasonal climatology for each season in a given year.

    Parameters
    ----------
    ds : xr.Dataset
        Input xarray Dataset
    data_var : str
        name of variable (dataArray)
    season : str
        A string representing a custom season (e.g., "MJJ"). Must consist of one or more month abbreviations.
    method : str, optional
        method for yearly average, by default "xcdat", optional alternative is "xcdat"

    Returns
    -------
    xr.Dataset
        xarray Dataset that contains timeseries of seasonal mean departure for each year
    """

    ds_yearly_means = custom_season_average(ds, data_var, season.upper(), method=method)
    ds_yearly_means = ds_yearly_means.bounds.add_missing_bounds()

    if "F" in season.upper():
        # If February included, consider weighting for leap year inclusion
        ds_clim = ds_yearly_means.temporal.average(data_var)
    else:
        # no weighting, mathmatical averaging
        time_key = get_time_key(ds_yearly_means)
        ds_clim = ds_yearly_means.mean(dim=time_key)

    ds_anomaly = ds_yearly_means.copy()
    ds_anomaly[data_var] = ds_yearly_means[data_var] - ds_clim[data_var]

    return ds_anomaly
