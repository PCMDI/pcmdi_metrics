"""
Functions to calculate atmospheric blocking metrics.

Computes regional and seasonal statistics from binary blocking masks,
including number of events (via connected component analysis) and
average size (in degree²).

Created by: Elina Valkonen (November 2023)
Updates by: Jiwoo Lee (November 2023)
Adapted for PMP by: Claude (November 2026)

References
----------
Wiedenmann, J. M., Lupo, A. R., Mokhov, I. I., & Tikhonova, E. A. (2002).
The climatology of blocking anticyclones for the Northern and Southern
Hemispheres: Block intensity as a diagnostic. Journal of Climate, 15(23),
3459-3473.
"""

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import label


def compute_blocking_metrics(
    ds: xr.Dataset,
    var: str = "pval_binary",
    historical: bool = False,
    regions: Optional[Dict[str, Dict[str, slice]]] = None,
    output_file: Optional[str] = None,
    verbose: bool = True,
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Calculate blocking frequency, count, and size by region and season.

    Computes blocking statistics for 6 regions and 4 seasons using connected
    component analysis. Default regions follow Wiedenmann et al. (2002).

    Parameters
    ----------
    ds : xr.Dataset
        Dataset with blocking mask from detect_blocking(). Must have 'time',
        'lat', 'lon' dimensions.
    var : str, optional
        Binary blocking mask variable name. Default 'pval_binary'.
    historical : bool, optional
        Period selection for spatial means:
        - True: Use full time period
        - False: Use 2070-2100 for future scenarios
        Default False.
    regions : dict, optional
        Custom region definitions as {name: {lat: slice, lon: slice}}.
        If None, uses default 6 regions:
        - NH: Continent (40E-140E), Pacific (140E-100W), Atlantic (100W-40E)
        - SH: Indian (30E-130E), Pacific (130E-60W), Atlantic (60W-30E)
    output_file : str, optional
        If provided, save spatial means to this NetCDF file. Default None (no save).
    verbose : bool, optional
        Print progress messages. Default True.

    Returns
    -------
    metrics_df : pd.DataFrame
        Metrics with columns:
        - Year : int
        - Season : str (DJF, MAM, JJA, SON)
        - Region : str (NC, NP, NA, SC, SP, SA) or custom names
        - Number : int (count of blocking events via connected components)
        - Size : float (average area of events in degree²)
    spatial_means : np.ndarray
        Shape (4, nlat, nlon) - mean blocking frequency for each season.
        Order: [DJF, MAM, JJA, SON]

    Notes
    -----
    - Blocking events identified via scipy.ndimage.label (26-connectivity)
    - Size calculated as: 2.0 (degree²) × grid cell count / event count
    - Regions with longitude wrap (Atlantic) handled via roll
    - For historical: spatial means computed over full period
    - For scenarios: spatial means computed 2070-2100 only

    Examples
    --------
    Compute metrics with default regions:

    >>> from pcmdi_metrics.blocking import detect_blocking, compute_blocking_metrics
    >>>
    >>> blocking = detect_blocking(ds, start='1979-01', end='2014-12')
    >>> metrics, spatial = compute_blocking_metrics(blocking, historical=True)
    >>>
    >>> # Annual mean by region
    >>> print(metrics.groupby('Region')['Number'].mean())
    >>>
    >>> # Seasonal means
    >>> print(metrics.groupby('Season')[['Number', 'Size']].mean())

    Custom regions:

    >>> custom_regions = {
    ...     'North_America': {'lat': slice(30, 70), 'lon': slice(230, 290)},
    ...     'Europe': {'lat': slice(35, 70), 'lon': slice(350, 40)}
    ... }
    >>> metrics, spatial = compute_blocking_metrics(
    ...     blocking,
    ...     regions=custom_regions
    ... )

    Save spatial means to file:

    >>> metrics, spatial = compute_blocking_metrics(
    ...     blocking,
    ...     output_file='blocking_spatial_means.nc'
    ... )

    See Also
    --------
    detect_blocking : Neural network blocking detection
    metrics_to_json : Save metrics in PCMDI JSON format
    """
    # Validate input
    if not isinstance(ds, xr.Dataset):
        raise TypeError(
            f"Input must be an xarray.Dataset, got {type(ds).__name__}.\n"
            "Use detect_blocking() to generate blocking dataset."
        )

    if var not in ds.data_vars:
        raise ValueError(
            f"Variable '{var}' not found in dataset.\n"
            f"Available variables: {list(ds.data_vars.keys())}"
        )

    # Initialize results
    results_df = pd.DataFrame(columns=["Year", "Season", "Region", "Number", "Size"])

    # Get spatial dimensions
    nlat = ds.sizes["lat"]
    nlon = ds.sizes["lon"]
    spatial_means = np.zeros((4, nlat, nlon))

    # Split by season
    djf, mam, jja, son = split_maps_by_month(ds, var)
    season_names = ["DJF", "MAM", "JJA", "SON"]

    if verbose:
        print("Computing metrics by season and region...")

    for season_idx, season_data in enumerate([djf, mam, jja, son]):
        season_name = season_names[season_idx]

        # Calculate spatial means
        if historical:
            # Use full time period for historical
            frequencymaps = season_data[var].values
            spatial_means[season_idx, :, :] = np.nanmean(frequencymaps, axis=0)
        else:
            # Use 2070-2100 for scenarios
            calendar = ds.time.dt.calendar
            if "360" in calendar:
                end_date = "2099-12-30"
            else:
                end_date = "2099-12-31"

            try:
                frequencymaps_subset = season_data.sel(
                    time=slice("2070-01-01", end_date)
                )
                spatial_means[season_idx, :, :] = np.nanmean(
                    frequencymaps_subset[var].values, axis=0
                )
            except (KeyError, ValueError):
                # If 2070-2100 not available, use full period
                if verbose:
                    print(
                        f"  Warning: 2070-2100 not available for {season_name}, "
                        "using full period"
                    )
                spatial_means[season_idx, :, :] = np.nanmean(
                    season_data[var].values, axis=0
                )

        # Group by year
        yearlydata = season_data.groupby("time.year")

        for year_value, year_data in yearlydata:
            if verbose and season_idx == 0 and year_value % 10 == 0:
                print(f"  Processing year {year_value}...")

            # Use default or custom regions
            if regions is None:
                region_list = split_regions(year_data, var)
                region_names = ["NC", "NP", "NA", "SC", "SP", "SA"]
            else:
                region_list, region_names = split_custom_regions(
                    year_data, var, regions
                )

            # Calculate metrics for each region
            for region_idx, region_data in enumerate(region_list):
                size_value = average_size(region_data, var)
                number_value = number_of_features(region_data, var)
                region_name = region_names[region_idx]

                # Append to dataframe
                new_row = pd.DataFrame(
                    [
                        [
                            int(year_value),
                            season_name,
                            region_name,
                            int(number_value),
                            float(size_value),
                        ]
                    ],
                    columns=results_df.columns,
                )
                results_df = pd.concat([results_df, new_row], ignore_index=True)

    if verbose:
        print(f"Metrics computed: {len(results_df)} rows")

    # Save spatial means if requested
    if output_file is not None:
        if verbose:
            print(f"Saving spatial means to {output_file}...")
        spatial_ds = create_spatial_means_dataset(ds, spatial_means, season_names)
        spatial_ds.to_netcdf(output_file)
        if verbose:
            print("Spatial means saved")

    return results_df, spatial_means


def split_maps_by_month(
    data: xr.Dataset, var: str
) -> Tuple[xr.Dataset, xr.Dataset, xr.Dataset, xr.Dataset]:
    """
    Split data into four seasons.

    Parameters
    ----------
    data : xr.Dataset
        Input dataset with time dimension.
    var : str
        Variable name to split.

    Returns
    -------
    tuple of xr.Dataset
        (DJF, MAM, JJA, SON) datasets.
    """
    # Extract each season
    DJF_blocks = data.sel(time=data.time.dt.season == "DJF")
    MAM_blocks = data.sel(time=data.time.dt.season == "MAM")
    JJA_blocks = data.sel(time=data.time.dt.season == "JJA")
    SON_blocks = data.sel(time=data.time.dt.season == "SON")

    return DJF_blocks, MAM_blocks, JJA_blocks, SON_blocks


def split_regions(
    season: xr.Dataset, var: str
) -> Tuple[xr.Dataset, xr.Dataset, xr.Dataset, xr.Dataset, xr.Dataset, xr.Dataset]:
    """
    Split data into 6 default regions (Wiedenmann et al. 2002).

    Northern Hemisphere:
    - NC (Continent): 40E-140E, 0-90N
    - NP (Pacific): 140E-100W (140-260), 0-90N
    - NA (Atlantic): 100W-40E (260-360+0-40), 0-90N

    Southern Hemisphere:
    - SC (Indian): 30E-130E, 90S-0
    - SP (Pacific): 130E-60W (130-300), 90S-0
    - SA (Atlantic): 60W-30E (300-360+0-30), 90S-0

    Parameters
    ----------
    season : xr.Dataset
        Seasonal dataset.
    var : str
        Variable name.

    Returns
    -------
    tuple of xr.Dataset
        (NC, NP, NA, SC, SP, SA) regional datasets.

    Notes
    -----
    Atlantic regions cross the prime meridian and require longitude rolling.
    """
    # Northern Hemisphere
    regionNC = season.sel(lat=slice(0, 90), lon=slice(40, 140))
    regionNP = season.sel(lat=slice(0, 90), lon=slice(140, 260))

    # NA region crosses 0° longitude, so shift longitudes
    rolleddata_NA = season.roll(lon=-40, roll_coords=False)
    regionNA = rolleddata_NA.sel(lat=slice(0, 90), lon=slice(220, 360))

    # Southern Hemisphere
    regionSC = season.sel(lat=slice(-90, 0), lon=slice(30, 130))
    regionSP = season.sel(lat=slice(-90, 0), lon=slice(130, 300))

    # SA region crosses 0° longitude, so shift longitudes
    rolleddata_SA = season.roll(lon=-30, roll_coords=False)
    regionSA = rolleddata_SA.sel(lat=slice(-90, 0), lon=slice(270, 360))

    return regionNC, regionNP, regionNA, regionSC, regionSP, regionSA


def split_custom_regions(
    season: xr.Dataset, var: str, regions: Dict[str, Dict[str, slice]]
) -> Tuple[list, list]:
    """
    Split data into custom regions.

    Parameters
    ----------
    season : xr.Dataset
        Seasonal dataset.
    var : str
        Variable name.
    regions : dict
        Region definitions as {name: {lat: slice, lon: slice}}.

    Returns
    -------
    region_list : list of xr.Dataset
        Regional datasets.
    region_names : list of str
        Region names.
    """
    region_list = []
    region_names = []

    for name, bounds in regions.items():
        lat_slice = bounds.get("lat", slice(None))
        lon_slice = bounds.get("lon", slice(None))

        region_data = season.sel(lat=lat_slice, lon=lon_slice)
        region_list.append(region_data)
        region_names.append(name)

    return region_list, region_names


def number_of_features(data: xr.Dataset, var: str) -> int:
    """
    Count number of distinct blocking events using connected component analysis.

    Uses scipy.ndimage.label with default connectivity (26-connectivity for 2D).
    Each spatially connected region of blocking (value=1) is counted as one event.

    Parameters
    ----------
    data : xr.Dataset
        Regional dataset.
    var : str
        Binary blocking mask variable name.

    Returns
    -------
    int
        Total number of blocking events across all time steps.

    Examples
    --------
    >>> n_events = number_of_features(region_data, 'pval_binary')
    >>> print(f"Found {n_events} blocking events")
    """
    numbers = 0

    for timestep in data[var].values:
        labeled_array, num_features = label(timestep)
        numbers += num_features

    return numbers


def average_size(data: xr.Dataset, var: str) -> float:
    """
    Calculate average size of blocking events in degree².

    Size is computed as the number of grid cells × grid spacing (2°×2°).
    Each event is identified via connected component labeling.

    Parameters
    ----------
    data : xr.Dataset
        Regional dataset.
    var : str
        Binary blocking mask variable name.

    Returns
    -------
    float
        Mean blocking event size in degree². Returns NaN if no events found.

    Notes
    -----
    - Grid spacing assumed to be 2°×2° (from regridding in detect_blocking)
    - Size = 2.0 × (total grid cells in events) / (number of events)
    - Background (label=0) is excluded from size calculation

    Examples
    --------
    >>> mean_size = average_size(region_data, 'pval_binary')
    >>> print(f"Average blocking size: {mean_size:.1f} degree²")
    """
    degreesize = 2.0  # Grid spacing in degrees
    sizes = np.zeros(data[var].shape[0])

    for n, timestep in enumerate(data[var].values):
        labeled_array, num_features = label(timestep)

        if num_features == 0:
            sizes[n] = np.nan
        else:
            # Count pixels for each label (excluding background=0)
            values, counts = np.unique(labeled_array, return_counts=True)
            # Sum size of all events and divide by number of events
            sizes[n] = np.sum(degreesize * counts[1:]) / num_features

    mean_size = np.nanmean(sizes)
    return mean_size


def create_spatial_means_dataset(
    original_ds: xr.Dataset, spatial_means: np.ndarray, season_names: list
) -> xr.Dataset:
    """
    Create xarray Dataset for spatial mean blocking frequency.

    Parameters
    ----------
    original_ds : xr.Dataset
        Original blocking dataset (for coordinates).
    spatial_means : np.ndarray
        Array with shape (4, nlat, nlon).
    season_names : list of str
        Season names ['DJF', 'MAM', 'JJA', 'SON'].

    Returns
    -------
    xr.Dataset
        Dataset with 'blocking_frequency' variable.
    """
    ds = xr.Dataset(
        {
            "blocking_frequency": (
                ("season", "lat", "lon"),
                spatial_means,
                {
                    "long_name": "Mean blocking frequency",
                    "units": "1",
                    "description": "Fraction of time with blocking present (0-1)",
                },
            )
        },
        coords={
            "season": season_names,
            "lat": original_ds.lat,
            "lon": original_ds.lon,
        },
    )

    ds.attrs["description"] = "Seasonal mean blocking frequency"
    ds.attrs["method"] = "Connected component analysis"

    return ds


def metrics_to_csv(
    metrics_df: pd.DataFrame, output_file: str, include_index: bool = False
) -> None:
    """
    Save blocking metrics DataFrame to CSV.

    Parameters
    ----------
    metrics_df : pd.DataFrame
        Metrics from compute_blocking_metrics().
    output_file : str
        Output CSV file path.
    include_index : bool, optional
        Include DataFrame index in output. Default False.

    Examples
    --------
    >>> metrics, spatial = compute_blocking_metrics(blocking)
    >>> metrics_to_csv(metrics, 'blocking_metrics.csv')
    """
    metrics_df.to_csv(output_file, index=include_index)


def spatial_means_to_npy(spatial_means: np.ndarray, output_file: str) -> None:
    """
    Save spatial means array to NumPy format.

    Parameters
    ----------
    spatial_means : np.ndarray
        Array from compute_blocking_metrics(), shape (4, nlat, nlon).
    output_file : str
        Output .npy file path.

    Examples
    --------
    >>> metrics, spatial = compute_blocking_metrics(blocking)
    >>> spatial_means_to_npy(spatial, 'blocking_spatial_means.npy')
    """
    np.save(output_file, spatial_means)


def metrics_to_json(
    metrics_df: pd.DataFrame,
    output_file: str,
    model_name: str,
    realm: str = "atmos",
    frequency: str = "day",
    reference_name: Optional[str] = None,
    provenance: Optional[Dict] = None,
) -> None:
    """
    Save blocking metrics to PCMDI-standard JSON format.

    Creates JSON with DIMENSIONS, RESULTS, and PROVENANCE sections following
    PMP conventions for model evaluation metrics.

    Parameters
    ----------
    metrics_df : pd.DataFrame
        Metrics from compute_blocking_metrics() with columns:
        Year, Season, Region, Number, Size
    output_file : str
        Output JSON file path.
    model_name : str
        Model identifier (e.g., 'CESM2', 'ACCESS-CM2').
    realm : str, optional
        Realm identifier. Default 'atmos'.
    frequency : str, optional
        Temporal frequency. Default 'day'.
    reference_name : str, optional
        Reference dataset name for comparison (e.g., 'ERA5').
        If None, output is model-only.
    provenance : dict, optional
        Additional provenance information. If None, generates default.

    Examples
    --------
    >>> from pcmdi_metrics.blocking import compute_blocking_metrics, metrics_to_json
    >>>
    >>> metrics, spatial = compute_blocking_metrics(blocking)
    >>> metrics_to_json(
    ...     metrics,
    ...     'CESM2_blocking_metrics.json',
    ...     model_name='CESM2',
    ...     reference_name='ERA5'
    ... )

    See Also
    --------
    compute_blocking_metrics : Generate metrics DataFrame
    """
    import json
    from collections import OrderedDict

    # Generate provenance if not provided
    if provenance is None:
        from pcmdi_metrics.io.base import generateProvenance

        provenance = generateProvenance()

    # Create DIMENSIONS section
    dimensions = OrderedDict()
    dimensions["json_structure"] = [
        "model",
        "reference" if reference_name else None,
        "season",
        "region",
        "statistic",
    ]
    dimensions["json_structure"] = [x for x in dimensions["json_structure"] if x]

    dimensions["season"] = {
        "DJF": "December-January-February",
        "MAM": "March-April-May",
        "JJA": "June-July-August",
        "SON": "September-October-November",
    }

    regions = metrics_df["Region"].unique()
    dimensions["region"] = {r: f"Blocking region {r}" for r in regions}

    dimensions["statistic"] = {
        "number": "Number of blocking events (connected components)",
        "size": "Average blocking size (degree²)",
        "mean_number": "Mean number of events per year",
        "mean_size": "Mean blocking size per year (degree²)",
    }

    # Create RESULTS section
    results = OrderedDict()
    results[model_name] = OrderedDict()

    # Group by season and region
    for season in ["DJF", "MAM", "JJA", "SON"]:
        season_data = metrics_df[metrics_df["Season"] == season]

        if len(season_data) == 0:
            continue

        results[model_name][season] = OrderedDict()

        for region in regions:
            region_data = season_data[season_data["Region"] == region]

            if len(region_data) == 0:
                continue

            results[model_name][season][region] = OrderedDict()

            # Calculate statistics
            number_values = region_data["Number"].values
            size_values = region_data["Size"].values

            # Remove NaN from size calculations
            size_values_clean = size_values[~np.isnan(size_values)]

            results[model_name][season][region]["number"] = OrderedDict(
                {
                    "values": number_values.tolist(),
                    "mean": float(np.mean(number_values)),
                    "std": float(np.std(number_values)),
                    "years": region_data["Year"].values.tolist(),
                }
            )

            results[model_name][season][region]["size"] = OrderedDict(
                {
                    "values": size_values.tolist(),
                    "mean": (
                        float(np.nanmean(size_values))
                        if len(size_values_clean) > 0
                        else None
                    ),
                    "std": (
                        float(np.nanstd(size_values))
                        if len(size_values_clean) > 0
                        else None
                    ),
                    "years": region_data["Year"].values.tolist(),
                }
            )

            # Overall mean statistics
            results[model_name][season][region]["mean_number"] = float(
                np.mean(number_values)
            )
            if len(size_values_clean) > 0:
                results[model_name][season][region]["mean_size"] = float(
                    np.nanmean(size_values)
                )
            else:
                results[model_name][season][region]["mean_size"] = None

    # Add reference data if provided
    if reference_name:
        # Placeholder for reference - would need actual reference metrics
        results["REFERENCE"] = reference_name

    # Create metadata section
    metadata = OrderedDict()
    metadata["metric"] = "Atmospheric Blocking"
    metadata["method"] = "U-Net neural network with ResNet152 backbone"
    metadata["realm"] = realm
    metadata["frequency"] = frequency
    metadata["regions"] = "Wiedenmann et al. (2002) 6-region definition"
    metadata["threshold"] = 0.34
    metadata["model_file"] = "falco_fulldata_oct11.h5"
    metadata["references"] = [
        "Valkonen, E., Lee, J., et al. (2023). U-Net based atmospheric blocking detection.",
        "Wiedenmann, J. M., et al. (2002). The climatology of blocking anticyclones. J. Climate, 15(23), 3459-3473.",
    ]

    # Combine into final JSON structure
    output_json = OrderedDict()
    output_json["DIMENSIONS"] = dimensions
    output_json["RESULTS"] = results
    output_json["METADATA"] = metadata
    output_json["PROVENANCE"] = provenance

    # Write to file
    with open(output_file, "w") as f:
        json.dump(output_json, f, indent=2)

    print(f"Metrics saved to: {output_file}")
