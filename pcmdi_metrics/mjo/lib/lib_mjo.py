"""
Code written by Jiwoo Lee, LLNL. Feb. 2019
Inspired by Daehyun Kim and Min-Seop Ahn's MJO metrics.

Reference:
Ahn, MS., Kim, D., Sperber, K.R. et al. Clim Dyn (2017) 49: 4023.
https://doi.org/10.1007/s00382-017-3558-4
"""
from __future__ import print_function
import cdms2
import cdtime
import cdutil
import MV2
import numpy as np
import pcmdi_metrics
from scipy import signal


def interp2commonGrid(d, dlat, debug=False):
    """
    input
    - d: cdms array
    - dlat: resolution (i.e. grid distance) in degree
    output
    - d2: d interpolated to dlat resolution grid
    """
    nlat = int(180/dlat)
    grid = cdms2.createGaussianGrid(nlat, xorigin=0.0, order="yx")
    d2 = d.regrid(grid, regridTool='regrid2', mkCyclic=True)
    d2 = d2(latitude=(-10, 10))
    if debug:
        print('debug: d2.shape:', d2.shape)
    return d2


def subSliceSegment(d, year, mon, day, length):
    """
    Note: From given cdms array (3D: time and spatial 2D)
          Subslice to get segment with given length starting from given time.
    input
    - d: cdms array
    - year: segment starting year (integer)
    - mon: segment starting month (integer)
    - day: segement starting day (integer)
    - length: segment length (integer)
    """
    tim = d.getTime()
    comTim = tim.asComponentTime()
    h = comTim[0].hour
    m = comTim[0].minute
    s = comTim[0].second
    cptime = cdtime.comptime(year, mon, day, h, m, s)  # start date of segment
    n = comTim.index(cptime)  # time dimension index of above start date
    d2 = d.subSlice((n, n+length))  # slie 180 time steps starting from above index
    return d2


def Remove_dailySeasonalCycle(d, d_cyc):
    """
    Note: Remove daily seasonal cycle
    input
    - d: cdms array
    - d_cyc: numpy array
    output
    - d2: cdms array
    """
    d2 = MV2.subtract(d, d_cyc)
    # Preserve Axes
    for i in range(len(d.shape)):
        d2.setAxis(i, d.getAxis(i))
    # Preserve variable id (How to preserve others?)
    d2.id = d.id
    return d2


def get_daily_ano_segment(d_seg):
    """
    Note: 1. Get daily time series (3D: time and spatial 2D)
          2. Meridionally average (2D: time and spatial, i.e., longitude)
          3. Get anomaly by removing time mean of the segment
    input
    - d_seg: cdms2 data
    output
    - d_seg_x_ano: 2d array
    """
    cdms2.setAutoBounds('on')
    # sub region
    d_seg = d_seg(latitude=(-10, 10))
    # Get meridional average (3d (t, y, x) to 2d (t, y))
    d_seg_x = cdutil.averager(d_seg, axis='y', weights='weighted')
    # Get time-average in the segment on each longitude grid
    d_seg_x_ave = cdutil.averager(d_seg_x, axis='t')
    # Remove time mean for each segment
    d_seg_x_ano = MV2.subtract(d_seg_x, d_seg_x_ave)
    return d_seg_x_ano


def space_time_spectrum(d_seg_x_ano):
    """
    input
    - d: 2d cdms MV2 array (t (time), n (space))
    output
    - p: 2d array for power
    NOTE: Below code taken from
    https://github.com/CDAT/wk/blob/2b953281c7a4c5d0ac2d79fcc3523113e31613d5/WK/process.py#L188
    """
    # Number of grid in longitude axis, and timestep for each segment
    NTSub = d_seg_x_ano.shape[0]  # NTSub
    NL = d_seg_x_ano.shape[1]  # NL
    # Tapering
    d_seg_x_ano = taper(d_seg_x_ano)
    # Power sepctrum analysis
    EE = np.fft.fft2(d_seg_x_ano, axes=(1, 0)) / float(NL) / float(NTSub)
    # Now the array EE(n,t) contains the (complex) space-time spectrum.
    """
    Create array PEE(NL+1,NT/2+1) which contains the (real) power spectrum.
    Note how the PEE array is arranged into a different order to EE.
    In this code, PEE is "Power", and its multiyear average will be "power"
    """
    # OK NOW THE LITTLE MAGIC WITH REORDERING !
    A = np.absolute(EE[0:NTSub // 2 + 1, 1:NL // 2 + 1])**2
    B = np.absolute(EE[NTSub // 2:NTSub, 1:NL // 2 + 1])**2
    C = np.absolute(EE[NTSub // 2:NTSub, 0:NL // 2 + 1])**2
    D = np.absolute(EE[0:NTSub // 2 + 1, 0:NL // 2 + 1])**2
    # Define returning array
    p = np.zeros((NTSub + 1, NL + 1), np.float)
    p[NTSub // 2:, :NL // 2] = A[:, ::-1]
    p[:NTSub // 2, :NL // 2] = B[:, ::-1]
    p[NTSub // 2 + 1:, NL // 2:] = C[::-1, :]
    p[:NTSub // 2 + 1, NL // 2:] = D[::-1, :]
    return p


def taper(data):
    """
    Note: taper first and last 45 days with cosine window, using scipy.signal function
    input
    - data: cdms 2d array (t, n) t: time, n: space (meridionally averaged)
    output:
    - data: tapered data
    """
    window = signal.tukey(len(data))
    data2 = data.copy()
    for i in range(0, len(data)):
        data2[i] = MV2.multiply(data[i][:], window[i])
    return data2


def decorate_2d_array_axes(a, y, x,
                           a_id=None, y_id=None, x_id=None,
                           y_units=None, x_units=None):
    """
    Note: Decorate array with given axes
    input
    - a: 2d cdms MV2 or numpy array to decorate axes
    - y: list of numbers to be axis 0
    - x: list of numbers to be axis 1
    - a_id: id of variable a
    - y_id, x_id: id of axes, string
    - y_units, x_units: units of axes
    output
    - return the given array, a, with axes attached
    """
    y = MV2.array(y)
    x = MV2.array(x)
    # Create the frequencies axis
    Y = cdms2.createAxis(y)
    Y.id = y_id
    Y.units = y_units
    # Create the wave numbers axis
    X = cdms2.createAxis(x)
    X.id = x_id
    X.units = x_units
    # Makes it an MV2 with axis and id (id come sfrom orignal data id)
    a = MV2.array(a, axes=(Y, X), id=a_id)
    return a


def generate_axes_and_decorate(Power, NT, NL):
    """
    Note: Generates axes for the decoration
    input
    - Power: 2d numpy array
    - NT: integer, number of time step
    - NL: integer, number of spatial grid
    output
    - Power: decorated 2d cdms array
    - ff: frequency axis
    - ss: wavenumber axis
    """
    # frequency
    ff = []
    for t in range(0, NT+1):
        ff.append(float(t-NT/2)/float(NT))
    ff = MV2.array(ff)
    ff.id = 'frequency'
    ff.units = 'cycles per day'
    # wave number
    ss = []
    for n in range(0, NL+1):
        ss.append(float(n)-float(NL/2))
    ss = MV2.array(ss)
    ss.id = 'zonalwavenumber'
    ss.units = '-'
    # Decoration
    Power = decorate_2d_array_axes(
        Power, ff, ss,
        a_id='power', y_id=ff.id, x_id=ss.id,
        y_units=ff.units, x_units=ss.units)
    return Power, ff, ss


def output_power_spectra(NL, NT, Power, ff, ss):
    """
    Below code taken and modified from Daehyun Kim's Fortran code (MSD/level_2/sample/stps/stps.sea.f.sample)
    """
    # The corresponding frequencies, ff, and wavenumbers, ss, are:-
    PEE = Power
    OEE = np.zeros((21, 11))
    for n in range(int(NL/2), int(NL/2)+1+10):
        nn = n - int(NL/2)
        for t in range(int(NT/2)-10, int(NT/2+1+10)):
            tt = -(int(NT/2)+1)+11+t
            OEE[tt, nn] = PEE[t, n]
    a = list((ff[i] for i in range(int(NT/2)-10, int(NT/2)+1+10)))
    b = list((ss[i] for i in range(int(NL/2), int(NL/2)+1+10)))
    a = MV2.array(a)
    b = MV2.array(b)
    # Decoration
    OEE = decorate_2d_array_axes(
        OEE, a, b,
        a_id='power', y_id=ff.id, x_id=ss.id,
        y_units=ff.units, x_units=ss.units)
    # Transpose for visualization
    OEE = MV2.transpose(OEE, (1, 0))
    OEE.id = 'power'
    return OEE


def write_netcdf_output(d, fname):
    """
    Note: write array in a netcdf file
    input
    - d: array
    - fname: string. directory path and name of the netcd file, without .nc
    """
    fo = cdms2.open(fname+'.nc', 'w')
    fo.write(d)
    fo.close()


def calculate_ewr(OEE):
    """
    According to DK's gs script (MSD/level_2/sample/stps/e.w.ratio.gs.sample),
    E/W ratio is calculated as below:
    'd amean(power,x=14,x=17,y=2,y=4)/aave(power,x=5,x=8,y=2,y=4)'
    where x for frequency and y for wavenumber.
    Actual ranges of frequency and wavenumber have been checked and applied.
    """
    east_power_domain = OEE(
        zonalwavenumber=(1, 3),
        frequency=(0.0166667, 0.0333333))
    west_power_domain = OEE(
        zonalwavenumber=(1, 3),
        frequency=(-0.0333333, -0.0166667))
    eastPower = np.average(np.array(east_power_domain))
    westPower = np.average(np.array(west_power_domain))
    ewr = eastPower / westPower
    return ewr, eastPower, westPower


def unit_conversion(data, UnitsAdjust):
    """
    Convert unit following given tuple using MV2
    input:
    - data: cdms array
    - UnitsAdjust: tuple with 4 elements
      e.g.: (True, 'multiply', 86400., 'mm d-1'): e.g., kg m-2 s-1 to mm d-1
            (False, 0, 0, 0): no unit conversion
    """
    if UnitsAdjust[0]:
        data = getattr(MV2, UnitsAdjust[1])(data, UnitsAdjust[2])
        data.units = UnitsAdjust[3]
    return data


def mjo_metrics_to_json(outdir, json_filename, result_dict, model=None, run=None, cmec_flag=False):
    # Open JSON
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'),
        json_filename)
    # Dict for JSON
    if (model is None and run is None):
        result_dict_to_json = result_dict
    else:
        # Preserve only needed dict branch
        result_dict_to_json = result_dict.copy()
        models_in_dict = list(result_dict_to_json['RESULTS'].keys())
        for m in models_in_dict:
            if m == model:
                runs_in_model_dict = list(result_dict_to_json['RESULTS'][m].keys())
                for r in runs_in_model_dict:
                    if r != run:
                        del result_dict_to_json['RESULTS'][m][r]
            else:
                del result_dict_to_json['RESULTS'][m]
    # Write selected dict to JSON
    JSON.write(
        result_dict_to_json,
        json_structure=[
            "model", "realization", "metric"],
        sort_keys=True, indent=4, separators=(',', ': '))
    if cmec_flag:
        JSON.write_cmec(indent=4, separators=(',', ': '))
