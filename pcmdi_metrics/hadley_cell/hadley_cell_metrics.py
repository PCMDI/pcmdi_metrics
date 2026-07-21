"""
Hadley Cell Metrics

Compute Hadley cell edge positions and meridional stream function.

Created By: Kristin Chang (December 2025)
Last Updated: July 2026

References:
Hur, I., Yoo, C., Yeh, S.-W., Kim, Y.-H., & Seo, K.-H. (2024). Processes driving the intermodel spread of the Southern Hemisphere Hadley Circulation expansion in CMIP6 models. Journal of Geophysical Research: Atmospheres, 129, e2024JD041726. https://doi.org/10.1029/2024JD041726
Hur, I., Kim, M., Kwak, K. et al. Hadley Circulation in the Present and Future Climate Simulations of the K-ACE Model. Asia-Pac J Atmos Sci 58, 353-363 (2022). https://doi.org/10.1007/s13143-021-00256-z
"""

from typing import Optional
from pathlib import Path
import numpy as np
import xarray as xr
from scipy import integrate, stats
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt


# Physical constants
GRAVITY = 9.81  # m/s²
EARTH_RADIUS = 6376.0e3  # m
DEGREES_TO_RADIANS = np.pi / 180.0

# Pressure level thresholds
HPA_LEVEL_FILTER = 5
PA_LEVEL_FILTER = 500
HPA_500 = 500
PA_500 = 50000

def hadley_cell_metrics(
    model_name: str,
    psl_data_path: str,
    vwnd_data_path: str,
    output_path: str,
    psl_ds_varname: str,
    vwnd_ds_varname: str,
    time_dim: str = 'time', 
    lon_dim: str = 'lon', 
    lat_dim: str = 'lat',
    level_dim: str = 'plev',
    regrid: Optional[bool] = False,
    target_grid: Optional[xr.Dataset] = None,
    regrid_tool: Optional[str] = None,
    regrid_method: Optional[str] = None
    
):
    """
    Calculates annual, seasonal, and monthly atmospheric meridional stream function (psi), 500 hPa psi cross section, and Hadle cell northern and southern hemipsher edge positions with linear trends.
    
    Parameters
    ----------
    model_name : str
        Name of model.
    psl_data_path : str
        Path to directory containing all sea level pressure netCDF files.
    vwnd_data_path : str
        Path to directory containing all meridional wind netCDF files.
    output_path: str
        Path to directory where output files will be saved.
    psl_varname : str
        Variable name for sea level pressure in input dataset.
    vwnd_varname : str
        Variable name for meridional wind in input dataset.
    time_dim : str
        Name of time dimension in dataset. Default is 'time'.
    lon_dim : str
        Name of longitude dimension in dataset. Default is 'lon'.
    lat_dim : str
        Name of latitude dimension in dataset. Default is 'lat'.
    level_dim : str
        Name of pressure level dimension in dataset. Default is 'plev'.
    regrid : bool, optional
        If True, regrid input datasets to target_grid using xcdat.
        Default is False.
    target_grid : xarray dataset, optional
        Target grid for regridding. Required if regrid=True.
        Default is None.
    regrid_tool : str, optional
        Regrid tool (e.g., 'xesmf'). Required if regrid=True.
        Default is None.
    regrid_method : str, optional
        Regrid method (e.g., 'bilinear'). Required if regrid=True.
        Default is None.
   
    Returns
    ----------
    - Three netcdf data files for monthly psi, annual edge positions, climatological 500 hPa cross section.
    - Seasonal psi PNG plot.

    Example
    ----------
    > from hadley_cell_metrics import hadley_cell_metrics
    > hadley_cell_metrics(model_name=model_name,
                        vwnd_data_path=vwnd_data_path,
                        vpsl_data_path=psl_data_path,
                        output_path=data_output_path,
                        psl_ds_varname='MSL',
                        vwnd_ds_varname='V',
                        time_dim='time',
                        lon_dim='lon',
                        lat_dim='lat',
                        level_dim='level',
                        target_grid=target_grid,
                        regrid_tool='xesmf',
                        regrid_method='bilinear',
                        regrid=True
                        )
    """
    
    # Load data
    vwnd_ds, ps_ds = open_and_combine_data(psl_data_path, vwnd_data_path)
    print(f'Opened: files in {psl_data_path} and {vwnd_data_path}')

    # Regrid if requested
    if regrid:
        if target_grid is None or regrid_tool is None or regrid_method is None:
            raise ValueError("target_grid, regrid_tool, and regrid_method must be provided when regrid=True")
        vwnd_datasets, ps_datasets = regrid_with_xcdat(
            vwnd_ds, ps_ds, vwnd_ds_varname, psl_ds_varname, target_grid, regrid_tool, regrid_method
            )
        print('Regridded vwnd and psl datasets to target_grid')
    else:
        vwnd_datasets = vwnd_ds
        ps_datasets = ps_ds
        print('Skip: regrid')

    # calculate meridional stream function (psi)
    vwndps_monthly_psi_file, psi, vwnd, lev, lat = compute_monthly_psi(model_name, output_path, vwnd_datasets, ps_datasets, lat_dim, lon_dim, time_dim, level_dim, psl_ds_varname, vwnd_ds_varname)
    
    # calculate edge and slope
    compute_annual_edges(vwndps_monthly_psi_file, model_name, level_dim, lat_dim, time_dim, output_path)
    
    # calculate 500hPa cross section and seasonal climatology of meridional stream function (psi) plot 
    compute_clim_psi(psi, lev, lat, model_name, output_path, time_dim, level_dim, lat_dim)

    return


def open_and_combine_data(psl_data_path, vwnd_data_path):
    """
    Load and combine netCDF datasets from directories provided.

    Parameters
    ----------
    psl_data_path : str
        Path to directory containing all sea level pressure netCDF files.
    vwnd_data_path : str
        Path to directory containing meridional wind netCDF files.
    
    Returns
    ----------
    tuple of xr.Dataset
        Tuple containing (vwnd_dataset, psl_dataset)

    Raises
    ------
    FileNotFoundError
        If no .nc files found in either directory.
    """
    
    vwnd_files = sorted(Path(vwnd_data_path).glob('*.nc'))
    psl_files = sorted(Path(psl_data_path).glob('*.nc'))

    if not vwnd_files:
        raise FileNotFoundError(f"No .nc files found in {vwnd_data_path}")
    if not psl_files:
        raise FileNotFoundError(f"No .nc files found in {psl_data_path}")

    vwnd_datasets = xr.open_mfdataset(vwnd_files, combine='by_coords')
    ps_datasets = xr.open_mfdataset(psl_files, combine='by_coords')

    return vwnd_datasets, ps_datasets


def regrid_with_xcdat(vwnd_datasets, ps_datasets, vwnd_ds_varname, psl_ds_varname, target_grid, regrid_tool, regrid_method):
    """
    Regrid datasets to target grid using xcdat.

    Parameters
    ----------
    vwnd_ds : xr.Dataset
        Meridional wind dataset.
    ps_ds : xr.Dataset
        Sea level pressure dataset.
    vwnd_varname : str
        Variable name for meridional wind in vwnd_ds.
    psl_varname : str
        Variable name for sea level pressure in ps_ds.
    target_grid : xr.Dataset
        Target grid for regridding.
    regrid_tool : str
        Regridding tool (e.g., "xesmf").
    regrid_method : str
        Regridding method (e.g., "bilinear").

    Returns
    -------
    tuple of xr.Dataset
        Tuple containing (regridded_vwnd, regridded_psl).
    """
    vwnd_regridded = vwnd_datasets.regridder.horizontal(vwnd_ds_varname, target_grid, tool=regrid_tool, method=regrid_method)
    ps_regridded = ps_datasets.regridder.horizontal(psl_ds_varname, target_grid, tool=regrid_tool, method=regrid_method)

    return vwnd_regridded, ps_regridded


def compute_monthly_psi(model_name, output_path, vwnd_datasets, ps_datasets, lat_dim, lon_dim, time_dim, level_dim, psl_ds_varname, vwnd_ds_varname):
    """
    Compute monthly meridional stream function.

    Calculates the atmospheric meridional stream function by integrating
    zonally-averaged meridional wind over pressure levels.

    Parameters
    ----------
    model_name : str
        Model name for output file naming.
    output_path : str
        Directory path for output file.
    vwnd_ds : xr.Dataset
        Meridional wind dataset.
    ps_ds : xr.Dataset
        Surface pressure dataset.
    lat_dim : str
        Name of latitude dimension.
    lon_dim : str
        Name of longitude dimension.
    time_dim : str
        Name of time dimension.
    level_dim : str
        Name of pressure level dimension.
    psl_varname : str
        Variable name for surface pressure.
    vwnd_varname : str
        Variable name for meridional wind.

    Returns
    -------
    tuple
        Tuple containing:
        - output_file_path (str): Path to saved netCDF file
        - psi (xr.DataArray): Stream function array
        - vwnd (xr.DataArray): Masked meridional wind array
        - lev (np.ndarray): Pressure levels
        - lat (np.ndarray): Latitude coordinates
    """
    filename = f"{model_name}_vwndps_monthly_psi"
    output_file_path = Path(output_path) / filename
    print(f"Monthly psi will be saved to: {output_file_path}")

    # Determine pressure level filter
    if vwnd_datasets[level_dim].units == 'hPa':
        level_filter = HPA_LEVEL_FILTER
    else:
        level_filter = PA_LEVEL_FILTER

    # Filter and sort by pressure level
    vwnd_ = vwnd_datasets[vwnd_ds_varname].where(vwnd_datasets[level_dim] > level_filter, drop=True)
    vwnd_ = vwnd_.sortby(level_dim, ascending=True)
    
    # Extract coordinates and variables
    lev = np.asarray(vwnd_[level_dim])
    lat = np.asarray(vwnd_datasets.variables[lat_dim][:])
    t = np.asarray(vwnd_datasets.variables[time_dim][:])
    ps = ps_datasets[psl_ds_varname]

    # Convert from hPa to Pa if needed & mask data below surface
    if vwnd_datasets[level_dim].units == 'hPa':
        p_np = np.array(vwnd_[level_dim])*1.e2 
    else:
        p_np = np.array(vwnd_[level_dim])
    
    ps_np = np.array(ps)
    v_np = np.array(vwnd_)
    vwnd = v_np

    for iii in range(len(t)):
        vtmp=1.0*v_np[iii,:,:,:]           
        vtmp=1.0*vtmp.transpose(2,1,0)
        pstmp=1.0*ps_np[iii,:,:]
        pstmp=1.0*pstmp.transpose(1,0)

        # make 3d arr
        ptmp3d=0.0*vtmp+p_np # build a 3D pressure field by broadcasting p_np (vertical levels) over lat, lon
        pstmp3d=0.0*vtmp # build a 3d surface pressure field by repeating ps over the vertical dimension
        for kkk in range(len(p_np)):
            pstmp3d[:,:,kkk]=pstmp
            
        # 3D boolean indexing 
        vtmp[ptmp3d > pstmp3d] = np.nan # set v to NaN wherever p > ps
        vtmp=vtmp.transpose(2,1,0)
        vwnd[iii,:,:,:]= vtmp    

    vwnd = xr.DataArray(vwnd,dims=[time_dim, level_dim, lat_dim, lon_dim])
    vwnd = vwnd.assign_coords(vwnd_.coords)

    print("Calculate: zonal mean")
    # zonal mean
    vzm = vwnd.mean(dim=lon_dim)

    print("Compute: psi")
    # compute psi 
    if vwnd[level_dim].max() > 2000: # Already in Pa
        lev_ = vwnd[level_dim]
    else:
        lev_ = vwnd[level_dim] * 1.e2 # In hPa, convert to Pa
    g = 9.81 #[m/s2 ]
    a0 = 6376.0e3
    psi_ = integrate.cumulative_trapezoid(vzm,lev_,axis=1,initial=0)
    psi_ = 2*np.pi*a0/g*psi_ *np.cos(lat[np.newaxis,np.newaxis,:]*np.pi/180.) #[kg/s]
    psi = xr.DataArray(psi_,dims=[time_dim, level_dim, lat_dim])
    psi = psi.assign_coords(vzm.coords)

    # Save to NetCDF
    output_file_path.unlink(missing_ok=True)
    ds = xr.Dataset({'psi': psi})
    ds.to_netcdf(output_file_path, format='NETCDF4')
    print(f"Saved: {output_file_path}")
    
    return output_file_path, psi, vwnd, lev, lat


def  compute_annual_edges(vwndps_monthly_psi_file, model_name, level_dim, lat_dim, time_dim, output_path):
    """
    Compute annual Hadley cell edge positions and trends.

    Identifies the latitude of Hadley cell edges as the zero-crossing of the
    500 hPa stream function near ±30° latitude, then calculates linear trends
    over the time series.

    Parameters
    ----------
    monthly_psi_file : str
        Path to netCDF file containing monthly stream function.
    model_name : str
        Model name for output file naming.
    level_dim : str
        Name of pressure level dimension.
    lat_dim : str
        Name of latitude dimension.
    time_dim : str
        Name of time dimension.
    output_path : str
        Directory path for output file.

    Returns
    -------
    None
        Creates netCDF file with edge_nh and edge_sh variables, each containing
        slope and p_value attributes.
    """
    ds = xr.open_dataset(vwndps_monthly_psi_file)
    ann = ds.resample({time_dim: "1YE"}).mean()

    # call annual mean psi 
    edge_filename = f"{model_name}_psi_annual_edge.nc"
    output_file_path = Path(output_path) / edge_filename
    print(f"Annual edges will be saved to: {output_file_path}")

    lat = ann[lat_dim]
    tim = ann[time_dim]
    ntim = len(tim)

    # SH edge (edge_sh)
    edge_sh = np.zeros(ntim)

    if ann[level_dim].units == 'hPa':
        level_filter = HPA_500
    else:
        level_filter = PA_500

    for i in range(ntim):
        if ann[lat_dim][0].values > ann[lat_dim][1].values:
            tmp = ann.sel({level_dim:level_filter, lat_dim:slice(-20, -40), time_dim:tim[i]})
        else:
            tmp = ann.sel({level_dim:level_filter, lat_dim:slice(-40, -20), time_dim:tim[i]})
        
        tmp = tmp.to_array()

        # Find positive part
        pos_indices = np.where(tmp >= 0, tmp, np.nan)
        ilat = np.where((lat >= -40) & (lat <= -20))[0]
        x1 = lat[ilat][np.nanargmin(pos_indices)]
        y1 = np.nanmin(pos_indices)

        # Find negative part
        neg_indices = np.where(tmp <= 0, tmp, np.nan)
        x2 = lat[ilat][np.nanargmax(neg_indices)]
        y2 = np.nanmax(neg_indices)
        
        # Calculate slope (a) and y-intercept (b)
        a = (y2 - y1) / (x2 - x1)
        b = -x1 * a + y1

        # Calculate edge_sh
        edge_sh[i] = -b / a

    # slope
    x = np.arange(1, ntim+1, 1)
    slp, intercept, r_value, p_value, std_err = stats.linregress(x, edge_sh)

    # save as xarray
    edge_sh = xr.DataArray(edge_sh,dims=[time_dim])
    edge_sh = edge_sh.assign_coords(ann[time_dim].coords)
    edge_sh.attrs["slope"] = slp  # [/yr]

    # NH edge (edge_nh)
    edge_nh = np.zeros(ntim)

    for i in range(ntim):
        if ann[lat_dim][0].values > ann[lat_dim][1].values:
            tmp = ann.sel({level_dim:level_filter, lat_dim:slice(40, 20), time_dim:tim[i]})
        else:
            tmp = ann.sel({level_dim:level_filter, lat_dim:slice(20, 40), time_dim:tim[i]})
        
        tmp = tmp.to_array()

        # Find positive part
        pos_indices = np.where(tmp >= 0, tmp, np.nan)
        ilat = np.where((lat >= 20) & (lat <= 40))[0]
        x1 = lat[ilat][np.nanargmin(pos_indices)]
        y1 = np.nanmin(pos_indices)

        # Find negative part
        neg_indices = np.where(tmp <= 0, tmp, np.nan)
        x2 = lat[ilat][np.nanargmax(neg_indices)]
        y2 = np.nanmax(neg_indices)

        # Calculate slope (a) and y-intercept (b)
        a = (y2 - y1) / (x2 - x1)
        b = -x1 * a + y1

        # Calculate edge_nh
        edge_nh[i] = -b / a

    # slope
    x = np.arange(1, ntim+1, 1)
    slp, _, _, _, _ = stats.linregress(x, edge_nh)

    # save as xarray
    edge_nh = xr.DataArray(edge_nh,dims=[time_dim])
    edge_nh = edge_nh.assign_coords(ann[time_dim].coords)
    edge_nh.attrs["slope"] = slp  # [/yr]

    # Save to NetCDF
    output_file_path.unlink(missing_ok=True)
    ds_out = xr.Dataset({'edge_nh': edge_nh, 'edge_sh': edge_sh})
    ds_out.to_netcdf(output_file_path, format='NETCDF4')
    print(f"Saved: {output_file_path}")


def compute_clim_psi(psi, lev, lat, model_name, output_path, time_dim, level_dim, lat_dim):
    """
    Compute and plot seasonal climatology of stream function.

    Calculates annual and seasonal (DJF, MAM, JJA, SON) climatological means
    of the meridional stream function and creates a multi-panel plot.

    Parameters
    ----------
    psi : xr.DataArray
        Monthly stream function array.
    lev : np.ndarray
        Pressure levels.
    lat : np.ndarray
        Latitude coordinates.
    model_name : str
        Model name for output file naming.
    output_path : str
        Directory path for output files.
    time_dim : str
        Name of time dimension.
    level_dim : str
        Name of pressure level dimension.
    lat_dim : str
        Name of latitude dimension.

    Returns
    -------
    None
        Creates PNG plot and netCDF file with 500 hPa cross section.
    """
    season = psi.groupby(f"{time_dim}.season").mean(time_dim)
    ann_clim = psi.mean(dim=time_dim)

    ss = ['ANN','DJF','JJA','MAM','SON']
    clm = xr.DataArray(np.zeros((5, len(lev), len(lat))), coords=[ss, lev, lat], dims=['season', level_dim, lat_dim])

    clm[0, :, :] = ann_clim
    clm[1:, :, :] = season

    vwndps_psi_filename = f"{model_name}_vwndps_clm_psi"
    output_path = Path(output_path) / vwndps_psi_filename
    print(f"vwndps_clm_psi will be saved to: {output_path}")

    # Plot by season
    # Fixed colorbar range
    vmin, vmax = -1.5e11, 1.5e11

    num_panels = len(ss)
    fig, axes = plt.subplots(1, num_panels, figsize=(20, 4))

    # Determine pressure units and set fixed y-axis range
    # Check if lev is in hPa or Pa
    if np.max(lev) > 10000:  # Likely in Pa
        ylim_bottom, ylim_top = 100000, 10000  # 1000 hPa to 100 hPa in Pa
        ylabel = 'Pressure [Pa]'
    else:  # Likely in hPa
        ylim_bottom, ylim_top = 1000, 100  # 1000 hPa to 100 hPa
        ylabel = 'Pressure [hPa]'

    for i in range(num_panels):
        ax = axes[i]
        # Use pcolormesh with actual coordinates instead of imshow
        img = ax.pcolormesh(lat, lev, clm[i, :, :], cmap='jet', shading='auto', vmin=vmin, vmax=vmax)
        ax.set_title(ss[i])
        ax.set_xlabel('Latitude [°]')
        if i == 0:  # Only label y-axis on first panel
            ax.set_ylabel(ylabel)

        # Set fixed y-axis range: 1000 hPa (bottom) to 100 hPa (top)
        ax.set_ylim(ylim_bottom, ylim_top)

    cbar = fig.colorbar(img, ax=axes, orientation='horizontal', fraction=0.02, pad=0.1)
    cbar.set_label('[kg /s]')

    plot_path = Path(output_path) / f'{model_name}_clim_psi_plot.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f'Plot saved to: {plot_path}')
    plt.close(fig)
    
    # save 500 hPa Cross Section
    if HPA_500 in clm[level_dim].values:
        level_500hpa = HPA_500 
    else:
        level_500hpa = PA_500
    clm5 = clm.sel({level_dim: level_500hpa})
    
    filename = f"{model_name}_vwndps_clm_psi500.nc"
    output_file_path = Path(output_path) / filename
    print(f"500 hPa cross section will be saved to: {output_file_path}")

    output_file_path.unlink(missing_ok=True)
    ds = xr.Dataset({'clm': clm5})
    ds.to_netcdf(output_file_path, format='NETCDF4')
    print(f"Saved: {output_file_path}")


def main():
    """Entry point when run as script."""
    hadley_cell_metrics()


if __name__ == "__main__":
    raise SystemExit(main())
