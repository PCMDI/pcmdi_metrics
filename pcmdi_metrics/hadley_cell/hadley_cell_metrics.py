"""
Hadley Cell Metrics

Compute Hadley cell edge positions and meridional stream function.

Created By: Kristin Chang (December 2025)
Last Updated: August 2026

References:
Hur, I., Yoo, C., Yeh, S.-W., Kim, Y.-H., & Seo, K.-H. (2024). Processes driving the intermodel spread of the Southern Hemisphere Hadley Circulation expansion in CMIP6 models. Journal of Geophysical Research: Atmospheres, 129, e2024JD041726. https://doi.org/10.1029/2024JD041726
Hur, I., Kim, M., Kwak, K. et al. Hadley Circulation in the Present and Future Climate Simulations of the K-ACE Model. Asia-Pac J Atmos Sci 58, 353-363 (2022). https://doi.org/10.1007/s13143-021-00256-z
"""

from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy import integrate, stats


def hadley_cell_metrics(
    vwnd_ds: xr.Dataset,
    ps_ds: xr.Dataset,
    vwnd_var: str,
    ps_var: str,
    output_dir: str,
    model_name: str,
    time_dim: str = "time",
    lon_dim: str = "lon",
    lat_dim: str = "lat",
    lev_dim: str = "plev",
) -> dict:
    """
    Calculate Hadley cell meridional stream function and edge positions.

    Parameters
    ----------
    vwnd_ds : xr.Dataset
        Meridional wind dataset.
    ps_ds : xr.Dataset
        Surface pressure dataset.
    vwnd_var : str
        Variable name for meridional wind.
    ps_var : str
        Variable name for surface pressure.
    output_dir : str
        Directory path for output files.
    model_name : str
        Model identifier for file naming.
    time_dim : str, optional
        Time dimension name. Default 'time'.
    lon_dim : str, optional
        Longitude dimension name. Default 'lon'.
    lat_dim : str, optional
        Latitude dimension name. Default 'lat'.
    lev_dim : str, optional
        Pressure level dimension name. Default 'plev'.

    Returns
    -------
    dict
        Dictionary with paths to output files:
        - 'monthly_psi': Monthly stream function netCDF
        - 'annual_edges': Annual edge positions netCDF
        - 'clim_psi500': Climatological 500 hPa cross section netCDF
        - 'clim_plot': Seasonal climatology PNG

    Examples
    --------
    >>> import xarray as xr
    >>> from pcmdi_metrics.hadley_cell import hadley_cell_metrics
    >>> vwnd = xr.open_mfdataset('path/to/va_*.nc')
    >>> ps = xr.open_mfdataset('path/to/ps_*.nc')
    >>> results = hadley_cell_metrics(
    ...     vwnd_ds=vwnd,
    ...     ps_ds=ps,
    ...     vwnd_var='va',
    ...     ps_var='ps',
    ...     output_dir='./output',
    ...     model_name='CESM2'
    ... )
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Compute monthly stream function
    psi, vwnd_masked = compute_stream_function(
        vwnd_ds, ps_ds, vwnd_var, ps_var, time_dim, lon_dim, lat_dim, lev_dim
    )
    monthly_file = output_path / f"{model_name}_monthly_psi.nc"
    psi.to_netcdf(monthly_file)
    print(f"Saved: {monthly_file}")

    # Compute annual edge positions
    edge_ds = compute_hadley_edges(psi, time_dim, lev_dim, lat_dim)
    edge_file = output_path / f"{model_name}_annual_edges.nc"
    edge_ds.to_netcdf(edge_file)
    print(f"Saved: {edge_file}")

    # Compute seasonal climatology
    clim_psi500, plot_file = compute_seasonal_climatology(
        psi, model_name, output_path, time_dim, lev_dim, lat_dim
    )
    clim_file = output_path / f"{model_name}_clim_psi500.nc"
    clim_psi500.to_netcdf(clim_file)
    print(f"Saved: {clim_file}")

    return {
        "monthly_psi": str(monthly_file),
        "annual_edges": str(edge_file),
        "clim_psi500": str(clim_file),
        "clim_plot": str(plot_file),
    }


def compute_stream_function(
    vwnd_ds: xr.Dataset,
    ps_ds: xr.Dataset,
    vwnd_var: str,
    ps_var: str,
    time_dim: str = "time",
    lon_dim: str = "lon",
    lat_dim: str = "lat",
    lev_dim: str = "plev",
) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Calculate atmospheric meridional stream function.

    Integrates zonally-averaged meridional wind over pressure levels
    using the formula:

    psi = (2*pi*a/g) * integral(v * cos(lat) dp)

    where a is Earth radius, g is gravity, v is meridional wind.

    Parameters
    ----------
    vwnd_ds : xr.Dataset
        Meridional wind dataset.
    ps_ds : xr.Dataset
        Surface pressure dataset.
    vwnd_var : str
        Variable name for meridional wind.
    ps_var : str
        Variable name for surface pressure.
    time_dim : str
        Time dimension name.
    lon_dim : str
        Longitude dimension name.
    lat_dim : str
        Latitude dimension name.
    lev_dim : str
        Pressure level dimension name.

    Returns
    -------
    psi : xr.DataArray
        Stream function in kg/s, dimensions (time, level, lat).
    vwnd_masked : xr.DataArray
        Meridional wind masked below surface.
    """
    # Extract and prepare data
    vwnd = vwnd_ds[vwnd_var]
    ps = ps_ds[ps_var]

    # Determine pressure units
    lev_units = vwnd[lev_dim].attrs.get("units", "Pa")
    is_hpa = lev_units == "hPa"

    # Filter near-surface levels and sort by pressure
    min_lev = 5 if is_hpa else 500
    vwnd = vwnd.where(vwnd[lev_dim] > min_lev, drop=True)
    vwnd = vwnd.sortby(lev_dim)

    # Convert pressure to Pa
    lev_pa = vwnd[lev_dim] * 100 if is_hpa else vwnd[lev_dim]
    ps_pa = ps * 100 if ps.max() < 2000 else ps  # Assume hPa if max < 2000

    # Mask wind below surface
    vwnd_masked = vwnd.where(lev_pa < ps_pa)

    # Compute zonal mean
    vzm = vwnd_masked.mean(dim=lon_dim)

    # Integrate over pressure
    psi_values = integrate.cumulative_trapezoid(
        vzm, lev_pa, axis=vzm.dims.index(lev_dim), initial=0
    )

    # Apply spherical geometry factor
    earth_radius = 6.376e6  # m
    gravity = 9.81  # m/s²
    lat_rad = np.deg2rad(vwnd[lat_dim])
    cos_lat = np.cos(lat_rad)

    psi_values = (2 * np.pi * earth_radius / gravity) * psi_values * cos_lat.values

    # Create DataArray
    psi = xr.DataArray(
        psi_values,
        coords=vzm.coords,
        dims=vzm.dims,
        name="psi",
        attrs={
            "long_name": "meridional stream function",
            "units": "kg/s",
            "description": "Atmospheric meridional overturning stream function",
        },
    )

    return psi, vwnd_masked


def compute_hadley_edges(
    psi: xr.DataArray,
    time_dim: str = "time",
    lev_dim: str = "plev",
    lat_dim: str = "lat",
) -> xr.Dataset:
    """
    Identify Hadley cell edge positions from zero-crossing of psi at 500 hPa.

    Edges are defined as the latitude where the stream function crosses zero
    near ±30° latitude, calculated annually with linear trends.

    Parameters
    ----------
    psi : xr.DataArray
        Monthly stream function.
    time_dim : str
        Time dimension name.
    lev_dim : str
        Pressure level dimension name.
    lat_dim : str
        Latitude dimension name.

    Returns
    -------
    xr.Dataset
        Dataset with 'edge_nh' and 'edge_sh' variables, each with
        'slope' and 'p_value' attributes.
    """
    # Annual mean
    psi_ann = psi.resample({time_dim: "YE"}).mean()

    # Select 500 hPa level
    lev_units = psi[lev_dim].attrs.get("units", "Pa")
    lev_500 = 500 if lev_units == "hPa" else 50000
    psi_500 = psi_ann.sel({lev_dim: lev_500})

    # Calculate edges for each year
    edge_nh = xr.apply_ufunc(
        _find_edge_position,
        psi_500,
        input_core_dims=[[lat_dim]],
        vectorize=True,
        kwargs={"lat": psi_500[lat_dim].values, "lat_range": (20, 40)},
    )

    edge_sh = xr.apply_ufunc(
        _find_edge_position,
        psi_500,
        input_core_dims=[[lat_dim]],
        vectorize=True,
        kwargs={"lat": psi_500[lat_dim].values, "lat_range": (-40, -20)},
    )

    # Calculate trends
    years = np.arange(1, len(psi_500[time_dim]) + 1)
    slope_nh, _, _, p_nh, _ = stats.linregress(years, edge_nh.values)
    slope_sh, _, _, p_sh, _ = stats.linregress(years, edge_sh.values)

    # Package as dataset
    edge_nh.attrs = {"slope": slope_nh, "p_value": p_nh, "units": "degrees_north"}
    edge_sh.attrs = {"slope": slope_sh, "p_value": p_sh, "units": "degrees_north"}

    return xr.Dataset({"edge_nh": edge_nh, "edge_sh": edge_sh})


def _find_edge_position(
    psi_slice: np.ndarray, lat: np.ndarray, lat_range: Tuple[float, float]
) -> float:
    """
    Find latitude where psi crosses zero within lat_range via linear interpolation.

    Parameters
    ----------
    psi_slice : np.ndarray
        1D array of stream function values.
    lat : np.ndarray
        Latitude coordinates.
    lat_range : tuple
        (lat_min, lat_max) search range.

    Returns
    -------
    float
        Edge position in degrees.
    """
    lat_min, lat_max = sorted(lat_range)
    mask = (lat >= lat_min) & (lat <= lat_max)
    psi_sub = psi_slice[mask]
    lat_sub = lat[mask]

    # Find sign change
    pos_mask = psi_sub >= 0
    if not np.any(pos_mask) or not np.any(~pos_mask):
        return np.nan

    # Get closest positive and negative values
    x1 = lat_sub[pos_mask][np.argmin(psi_sub[pos_mask])]
    y1 = psi_sub[pos_mask].min()
    x2 = lat_sub[~pos_mask][np.argmax(psi_sub[~pos_mask])]
    y2 = psi_sub[~pos_mask].max()

    # Linear interpolation to zero
    if x2 != x1:
        edge = x1 - y1 * (x2 - x1) / (y2 - y1)
    else:
        edge = np.nan

    return edge


def compute_seasonal_climatology(
    psi: xr.DataArray,
    model_name: str,
    output_path: Path,
    time_dim: str = "time",
    lev_dim: str = "plev",
    lat_dim: str = "lat",
) -> Tuple[xr.Dataset, Path]:
    """
    Calculate and plot seasonal climatology of stream function.

    Parameters
    ----------
    psi : xr.DataArray
        Monthly stream function.
    model_name : str
        Model identifier.
    output_path : Path
        Output directory.
    time_dim : str
        Time dimension name.
    lev_dim : str
        Pressure level dimension name.
    lat_dim : str
        Latitude dimension name.

    Returns
    -------
    clim_psi500 : xr.Dataset
        500 hPa seasonal climatology.
    plot_path : Path
        Path to saved plot.
    """
    # Seasonal and annual means
    psi_seasonal = psi.groupby(f"{time_dim}.season").mean(time_dim)
    psi_annual = psi.mean(dim=time_dim)

    # Add season dimension to annual mean for concatenation
    psi_annual_expanded = psi_annual.expand_dims({"season": ["ANN"]})

    # Combine into single array
    seasons = ["ANN", "DJF", "JJA", "MAM", "SON"]
    clim_all = xr.concat(
        [psi_annual_expanded] + [psi_seasonal.sel(season=s) for s in seasons[1:]],
        dim=xr.DataArray(seasons, dims="season", name="season"),
    )

    # Extract 500 hPa
    lev_units = psi[lev_dim].attrs.get("units", "Pa")
    lev_500 = 500 if lev_units == "hPa" else 50000
    clim_psi500 = clim_all.sel({lev_dim: lev_500})

    # Plot
    plot_path = _plot_seasonal_psi(clim_all, model_name, output_path, lev_dim, lat_dim)

    return xr.Dataset({"psi": clim_psi500}), plot_path


def _plot_seasonal_psi(
    clim: xr.DataArray, model_name: str, output_path: Path, lev_dim: str, lat_dim: str
) -> Path:
    """
    Create multi-panel seasonal plot of stream function.

    Parameters
    ----------
    clim : xr.DataArray
        Climatological stream function with season dimension.
    model_name : str
        Model identifier.
    output_path : Path
        Output directory.
    lev_dim : str
        Pressure level dimension name.
    lat_dim : str
        Latitude dimension name.

    Returns
    -------
    Path
        Path to saved plot.
    """
    seasons = clim.season.values
    num_seasons = len(seasons)

    fig, axes = plt.subplots(1, num_seasons, figsize=(4 * num_seasons, 4))
    if num_seasons == 1:
        axes = [axes]

    # Determine pressure units
    lev = clim[lev_dim].values
    if np.max(lev) > 10000:
        ylim = (100000, 10000)
        ylabel = "Pressure [Pa]"
    else:
        ylim = (1000, 100)
        ylabel = "Pressure [hPa]"

    vmin, vmax = -1.5e11, 1.5e11

    for i, season in enumerate(seasons):
        ax = axes[i]
        data = clim.sel(season=season)

        img = ax.pcolormesh(
            data[lat_dim],
            data[lev_dim],
            data,
            cmap="jet",
            shading="auto",
            vmin=vmin,
            vmax=vmax,
        )
        ax.set_title(season)
        ax.set_xlabel("Latitude [°]")
        ax.set_ylim(ylim)

        if i == 0:
            ax.set_ylabel(ylabel)

    cbar = fig.colorbar(img, ax=axes, orientation="horizontal", fraction=0.02, pad=0.25)
    cbar.set_label("Stream function [kg/s]", labelpad=12)

    plot_path = output_path / f"{model_name}_seasonal_psi.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {plot_path}")

    return plot_path


def main():
    """Entry point when run as script."""
    raise NotImplementedError(
        "Use hadley_cell_metrics() function with xarray datasets as inputs. "
        "See function docstring for examples."
    )


if __name__ == "__main__":
    raise SystemExit(main())
