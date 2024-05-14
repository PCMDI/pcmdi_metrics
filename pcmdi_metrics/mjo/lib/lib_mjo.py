"""
Code written by Jiwoo Lee, LLNL. Feb. 2019
Inspired by Daehyun Kim and Min-Seop Ahn's MJO metrics.

Code update history
2024-05 converted to use xcdat as base building block (Jiwoo Lee)

Reference:
Ahn, MS., Kim, D., Sperber, K.R. et al. Clim Dyn (2017) 49: 4023.
https://doi.org/10.1007/s00382-017-3558-4
"""

from typing import Union

import numpy as np
import xarray as xr
from scipy import signal

from pcmdi_metrics.io import base, get_time_key, select_subset
from pcmdi_metrics.utils import create_target_grid, regrid


def interp2commonGrid(ds, data_var, dlat, dlon=None, debug=False):
    if dlon is None:
        dlon = dlat

    # Generate grid
    grid = create_target_grid(
        target_grid_resolution=f"{dlat}x{dlon}", grid_type="uniform"
    )

    # Regrid
    ds_regrid = regrid(ds, data_var, grid)
    ds_regrid_subset = select_subset(ds_regrid, lat=(-10, 10))

    if debug:
        print(
            "debug: ds_regrid_subset[data_var] shape:", ds_regrid_subset[data_var].shape
        )

    return ds_regrid_subset


def subSliceSegment(
    ds: Union[xr.Dataset, xr.DataArray], year: int, mon: int, day: int, length: int
) -> Union[xr.Dataset, xr.DataArray]:
    """
    Note: From given array (3D: time and spatial 2D)
          Subslice to get segment with given length starting from given time.
    input
    - ds: xarray dataset or dataArray
    - year: segment starting year (integer)
    - mon: segment starting month (integer)
    - day: segement starting day (integer)
    - length: segment length (integer)
    """

    time_key = get_time_key(ds)
    n = list(ds[time_key].values).index(
        ds.sel(time=f"{year:04}-{mon:02}-{day:02}")[time_key]
    )

    return ds.isel(
        time=slice(n, n + length)
    )  # slie 180 time steps starting from above index


def get_daily_ano_segment(d_seg: xr.Dataset, data_var: str) -> xr.Dataset:
    """
    Note: 1. Get daily time series (3D: time and spatial 2D)
          2. Meridionally average (2D: time and spatial, i.e., longitude)
          3. Get anomaly by removing time mean of the segment
    input
    - d_seg: xarray dataset
    - data_var: name of variable
    output
    - d_seg_x_ano: xarray dataset that contains 2d output array
    """
    # sub region
    d_seg = select_subset(d_seg, lat=(-10, 10))

    # Get meridional average (3d (t, y, x) to 2d (t, y))
    d_seg_x = d_seg.spatial.average(data_var, axis=["Y"])

    # Get time-average in the segment on each longitude grid
    d_seg_x_ave = d_seg_x.temporal.average(data_var)

    # Remove time mean for each segment
    d_seg_x_ano = d_seg.copy()
    d_seg_x_ano[data_var] = d_seg_x[data_var] - d_seg_x_ave[data_var]

    return d_seg_x_ano


def space_time_spectrum(d_seg_x_ano: xr.Dataset, data_var: str) -> np.ndarray:
    """
    input
    - d: xarray dataset that contains 2d DataArray (t (time), n (space)) named as `data_var`
    - data_var: name of the 2d DataArray
    output
    - p: 2d numpy array for power
    NOTE: Below code taken from
    https://github.com/CDAT/wk/blob/2b953281c7a4c5d0ac2d79fcc3523113e31613d5/WK/process.py#L188
    """
    # Number of grid in longitude axis, and timestep for each segment
    NTSub = d_seg_x_ano[data_var].shape[0]  # NTSub
    NL = d_seg_x_ano[data_var].shape[1]  # NL
    # Tapering
    d_seg_x_ano[data_var] = taper(d_seg_x_ano[data_var])
    # Power sepctrum analysis
    EE = np.fft.fft2(d_seg_x_ano[data_var], axes=(1, 0)) / float(NL) / float(NTSub)
    # Now the array EE(n,t) contains the (complex) space-time spectrum.
    """
    Create array PEE(NL+1,NT/2+1) which contains the (real) power spectrum.
    Note how the PEE array is arranged into a different order to EE.
    In this code, PEE is "Power", and its multiyear average will be "power"
    """
    # OK NOW THE LITTLE MAGIC WITH REORDERING !
    A = np.absolute(EE[0 : NTSub // 2 + 1, 1 : NL // 2 + 1]) ** 2
    B = np.absolute(EE[NTSub // 2 : NTSub, 1 : NL // 2 + 1]) ** 2
    C = np.absolute(EE[NTSub // 2 : NTSub, 0 : NL // 2 + 1]) ** 2
    D = np.absolute(EE[0 : NTSub // 2 + 1, 0 : NL // 2 + 1]) ** 2
    # Define returning array
    p = np.zeros((NTSub + 1, NL + 1), np.float)
    p[NTSub // 2 :, : NL // 2] = A[:, ::-1]
    p[: NTSub // 2, : NL // 2] = B[:, ::-1]
    p[NTSub // 2 + 1 :, NL // 2 :] = C[::-1, :]
    p[: NTSub // 2 + 1, NL // 2 :] = D[::-1, :]
    return p


def taper(data):
    """
    Note: taper first and last 45 days with cosine window, using scipy.signal function
    input
    - data: 2d array (t, n) t: time, n: space (meridionally averaged)
    output:
    - data: tapered data
    """
    window = signal.windows.tukey(len(data))
    data2 = data.copy()
    for i in range(0, len(data)):
        data2[i] = np.multiply(data[i][:], window[i])
    return data2


def generate_axes_and_decorate(Power, NT: int, NL: int) -> xr.DataArray:
    """
    Note: Generates axes for the decoration
    input
    - Power: 2d numpy array
    - NT: integer, number of time step
    - NL: integer, number of spatial grid
    output
    - xr.DataArray that contains Power 2d DataArray that has frequency and zonalwavenumber axes
    """
    # frequency
    ff = []
    for t in range(0, NT + 1):
        ff.append(float(t - NT / 2) / float(NT))
    ff = np.array(ff)

    # wave number
    ss = []
    for n in range(0, NL + 1):
        ss.append(float(n) - float(NL / 2))
    ss = np.array(ss)

    # Add name attributes to x and y coordinates
    x_coords = xr.IndexVariable(
        "zonalwavenumber", ss, attrs={"name": "zonalwavenumber", "units": "-"}
    )
    y_coords = xr.IndexVariable(
        "frequency", ff, attrs={"name": "frequency", "units": "cycles per day"}
    )

    # Create an xarray DataArray
    da = xr.DataArray(
        Power,
        coords={"frequency": y_coords, "zonalwavenumber": x_coords},
        dims=["frequency", "zonalwavenumber"],
        name="power",
    )

    return da


def output_power_spectra(NL: int, NT: int, Power):
    """
    Below code taken and modified from Daehyun Kim's Fortran code (MSD/level_2/sample/stps/stps.sea.f.sample)
    """
    # The corresponding frequencies, ff, and wavenumbers, ss, are:-
    PEE = Power

    ff = Power.frequency
    ss = Power.zonalwavenumber

    OEE = np.zeros((21, 11))
    for n in range(int(NL / 2), int(NL / 2) + 1 + 10):
        nn = n - int(NL / 2)
        for t in range(int(NT / 2) - 10, int(NT / 2 + 1 + 10)):
            tt = -(int(NT / 2) + 1) + 11 + t
            OEE[tt, nn] = PEE[t, n]
    a = list((ff[i] for i in range(int(NT / 2) - 10, int(NT / 2) + 1 + 10)))
    b = list((ss[i] for i in range(int(NL / 2), int(NL / 2) + 1 + 10)))
    a = np.array(a)
    b = np.array(b)
    # Decoration

    # Add name attributes to x and y coordinates
    x_coords = xr.IndexVariable(
        "zonalwavenumber", b, attrs={"name": "zonalwavenumber", "units": "-"}
    )
    y_coords = xr.IndexVariable(
        "frequency", a, attrs={"name": "frequency", "units": "cycles per day"}
    )

    # Create an xarray DataArray
    OEE = xr.DataArray(
        OEE,
        coords={"frequency": y_coords, "zonalwavenumber": x_coords},
        dims=["frequency", "zonalwavenumber"],
        name="power",
    )

    # Transpose for visualization
    # OEE = np.transpose(OEE, (1, 0))
    print("before transpose, OEE.shape:", OEE.shape)
    transposed_OEE = OEE.transpose()
    print("after transpose, transposed_OEE.shape:", transposed_OEE.shape)
    return transposed_OEE

    # return OEE


def write_netcdf_output(da: xr.DataArray, fname):
    """
    Note: write array in a netcdf file
    input
    - d: xr.DataArray object
    - fname: string of filename. Directory path that includes file name without .nc
    output
    - None
    """
    ds = xr.Dataset({da.name: da})
    ds.to_netcdf(fname + ".nc")


def calculate_ewr(OEE):
    """
    According to DK's gs script (MSD/level_2/sample/stps/e.w.ratio.gs.sample),
    E/W ratio is calculated as below:
    'd amean(power,x=14,x=17,y=2,y=4)/aave(power,x=5,x=8,y=2,y=4)'
    where x for frequency and y for wavenumber.
    Actual ranges of frequency and wavenumber have been checked and applied.
    """
    east_power_domain = OEE.sel(
        zonalwavenumber=slice(1, 3), frequency=slice(0.016, 0.034)
    )
    west_power_domain = OEE.sel(
        zonalwavenumber=slice(1, 3), frequency=slice(-0.034, -0.016)
    )
    eastPower = np.average(east_power_domain)
    westPower = np.average(west_power_domain)
    ewr = eastPower / westPower
    return ewr, eastPower, westPower


def mjo_metrics_to_json(
    outdir, json_filename, result_dict, model=None, run=None, cmec_flag=False
):
    # Open JSON
    JSON = base.Base(outdir, json_filename)
    # Dict for JSON
    if model is None and run is None:
        result_dict_to_json = result_dict
    else:
        # Preserve only needed dict branch
        result_dict_to_json = result_dict.copy()
        models_in_dict = list(result_dict_to_json["RESULTS"].keys())
        for m in models_in_dict:
            if m == model:
                runs_in_model_dict = list(result_dict_to_json["RESULTS"][m].keys())
                for r in runs_in_model_dict:
                    if r != run:
                        del result_dict_to_json["RESULTS"][m][r]
            else:
                del result_dict_to_json["RESULTS"][m]
    # Write selected dict to JSON
    JSON.write(
        result_dict_to_json,
        json_structure=["model", "realization", "metric"],
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    if cmec_flag:
        JSON.write_cmec(indent=4, separators=(",", ": "))
