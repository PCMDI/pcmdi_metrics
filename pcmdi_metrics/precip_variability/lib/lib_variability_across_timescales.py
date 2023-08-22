import copy
import math
import os
import sys

import cdutil
import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import chi2

import pcmdi_metrics

import xarray as xr
import xcdat
from xcdat.regridder import grid

# ==================================================================================
def precip_variability_across_timescale(
    file, syr, eyr, dfrq, mip, dat, var, fac, nperseg, noverlap, res, lat_range, lon_range, outdir, cmec
):
    """
    Regridding -> Anomaly -> Power spectra -> Domain&Frequency average -> Write
    """

    psdmfm = {"RESULTS": {}}

    f = xcdat.open_mfdataset(file)
    cal = f.time.encoding["calendar"]   
    if "360" in cal:
        ldy = 30
    else:
        ldy = 31
    print(dat, cal)
    print("syr, eyr:", syr, eyr)
    for iyr in range(syr, eyr + 1):
        print(iyr)
        do = f.sel(time=slice(str(iyr) + "-01-01 00:00:00",str(iyr) + "-12-" + str(ldy) + " 23:59:59"))
        
        # Regridding
        rgtmp = RegridHoriz(do, var, res)*float(fac)
        if len(lat_range) > 0 and len(lon_range) > 0:
            rgtmp = CropLatLon(rgtmp, lat_range, lon_range)
        if iyr == syr:
            drg = copy.deepcopy(rgtmp)
        else:
            drg = xr.concat([drg, rgtmp], dim='time')
        print(iyr, drg.shape)      
    nlon = str(len(drg.lon))
    nlat = str(len(drg.lat))

    f.close()

    # Anomaly
    if dfrq == "day":
        ntd = 1
    elif dfrq == "3hr":
        ntd = 8
    else:
        sys.exit("ERROR: dfrq " + dfrq + " is not defined!")
    clim, anom = ClimAnom(drg, ntd, syr, eyr, cal)

    # Power spectum of total
    freqs, ps, rn, sig95 = Powerspectrum(drg, nperseg, noverlap)
    # Domain & Frequency average
    psdmfm_forced = Avg_PS_DomFrq(ps, freqs, ntd, dat, mip, "forced")
    # Write data (nc file)
    outfilename = "PS_pr." + str(dfrq) + "_regrid." + nlon + "x" + nlat + "_" + dat + ".nc"
    custom_dataset = xr.merge([freqs, ps, rn, sig95])
    custom_dataset.to_netcdf(path=os.path.join(outdir(output_type="diagnostic_results"), outfilename))
        
    # Power spectum of anomaly
    freqs, ps, rn, sig95 = Powerspectrum(anom, nperseg, noverlap)
    # Domain & Frequency average
    psdmfm_unforced = Avg_PS_DomFrq(ps, freqs, ntd, dat, mip, "unforced")
    # Write data (nc file)
    outfilename = "PS_pr." + str(dfrq) + "_regrid." + nlon + "x" + nlat + "_" + dat + "_unforced.nc"
    custom_dataset = xr.merge([freqs, ps, rn, sig95])
    custom_dataset.to_netcdf(path=os.path.join(outdir(output_type="diagnostic_results"), outfilename))
        
    # Write data (json file)
    psdmfm["RESULTS"][dat] = {}
    psdmfm["RESULTS"][dat]["forced"] = psdmfm_forced
    psdmfm["RESULTS"][dat]["unforced"] = psdmfm_unforced

    outfilename = (
        "PS_pr." + str(dfrq) + "_regrid." + nlon + "x" + nlat + "_area.freq.mean_" + dat + ".json"
    )
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type="metrics_results"), outfilename
    )
    JSON.write(
        psdmfm,
        json_structure=["model+realization", "variability type", "domain", "frequency"],
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    if cmec:
        JSON.write_cmec(indent=4, separators=(",", ": "))


# ==================================================================================
def RegridHoriz(d, var, res):
    """
    Regrid to 2deg (180lon*90lat) horizontal resolution
    Input
    - d: xCDAT variable
    - var: variable name
    Output
    - drg: xCDAT variable with 2deg horizontal resolution
    """
    start_lat=-90.+res/2.
    start_lon=0.
    end_lat = 90.-res/2.
    end_lon = 360.-res
    nlat = ((end_lat - start_lat) * 1./res) + 1
    nlon = ((end_lon - start_lon) * 1./res) + 1

    tgrid = grid.create_uniform_grid(start_lat,end_lat,res,start_lon,end_lon,res)
    drg = d.regridder.horizontal(var, tgrid, tool="xesmf", method="conservative_normed",periodic=True)[var]
    
    print("Complete regridding from", d[var].shape, "to", drg.shape)
    return drg

# ==================================================================================
def CropLatLon(d,lat_range,lon_range):
    """
    Select a subgrid of the dataset defined by lat1, lat2, lon1, and lon2.
    Input
    - d: xCDAT variable
    - lat_range: list of floats
    - lon_range: list of floats
    Output
    - dnew: xCDAT variable selected over region of interest
    """
    lat1 = lat_range[0]
    lat2 = lat_range[1]
    lon1 = lon_range[0]
    lon2 = lon_range[1]

    try:
        dnew = d.sel(lat=slice(lat1,lat2), lon=slice(lon1,lon2))
    
    except Exception as e:
        print("Error:",e)
        print("Could not select lat/lon box",lat1,lat2,lon1,lon2)
        dnew = d

    return dnew

# ==================================================================================
def ClimAnom(d, ntd, syr, eyr, cal):
    """
    Calculate climatoloty and anomaly with data higher frequency than daily
    Input
    - d: xCDAT variable
    - ntd: number of time steps per day (daily: 1, 3-hourly: 8)
    - syr: analysis start year
    - eyr: analysis end year
    - cal: calendar
    Output
    - clim: climatology (climatological diurnal and annual cycles)
    - anom: anomaly departure from the climatological diurnal and annual cycles
    """
        
    # Year segment
    nyr = eyr - syr + 1
    if "gregorian" in cal:
        ndy = 366
        ldy = 31
        dseg = np.zeros((nyr, ndy, ntd, d.shape[1], d.shape[2]), dtype=float)
        for iyr, year in enumerate(range(syr, eyr + 1)):
            yrtmp = d.sel(time=slice(str(year) + "-01-01 00:00:00",str(year) + "-12-" + str(ldy) + " 23:59:59"))
                        
            expanded = yrtmp.expand_dims("ndy")          
            yrtmpseg = np.reshape(
                expanded, (int(yrtmp.shape[0] / ntd), ntd, yrtmp.shape[1], yrtmp.shape[2])
            )            
            
            if yrtmpseg.shape[0] == 365:
                dseg[iyr, 0:59] = yrtmpseg[0:59]
                dseg[iyr, 60:366] = yrtmpseg[59:365]
                dseg[iyr, 59] = np.nan
            else:
                dseg[iyr] = yrtmpseg
    else:
        if "360" in cal:
            ndy = 360
            ldy = 30
        else:  # 365-canlendar
            ndy = 365
            ldy = 31
        dseg = np.zeros((nyr, ndy, ntd, d.shape[1], d.shape[2]), dtype=float)        
        for iyr, year in enumerate(range(syr, eyr + 1)):
            yrtmp = d.sel(time=slice(str(year) + "-01-01 00:00:00",str(year) + "-12-" + str(ldy) + " 23:59:59"))            
            
            expanded = yrtmp.expand_dims("ndy")          
            yrtmpseg = np.reshape(
                expanded, (int(yrtmp.shape[0] / ntd), ntd, yrtmp.shape[1], yrtmp.shape[2])
            )            
            dseg[iyr] = yrtmpseg


    # Climatology
    clim = np.nanmean(dseg, axis=0)

    # Anomaly
    anom = np.array([])
    if "gregorian" in cal:
        for iyr, year in enumerate(range(syr, eyr + 1)):
            yrtmp = d.sel(time=slice(str(year) + "-01-01 00:00:00",str(year) + "-12-" + str(ldy) + " 23:59:59"))            
                        
            if yrtmp.shape[0] == 365 * ntd:
                anom = np.append(
                    anom,
                    (np.delete(dseg[iyr], 59, axis=0) - np.delete(clim, 59, axis=0)),
                )
            else:
                anom = np.append(anom, (dseg[iyr] - clim))
    else:
        for iyr, year in enumerate(range(syr, eyr + 1)):
            anom = np.append(anom, (dseg[iyr] - clim))

    # Reahape and Dimension information
    clim = np.reshape(clim, (ndy * ntd, d.shape[1], d.shape[2]))
    anom = np.reshape(anom, (d.shape[0], d.shape[1], d.shape[2]))
    
    climtime = pd.period_range(start="0001-01-01", periods=clim.shape[0], freq=str(24/ntd)+"H")
    clim = xr.DataArray(clim, coords=[climtime, d.coords[d.dims[1]], d.coords[d.dims[2]]], dims=d.dims)
    anom = xr.DataArray(anom, coords=d.coords, dims=d.dims)
    
    print("Complete calculating climatology and anomaly for calendar of", cal)
    return clim, anom


# ==================================================================================
def Powerspectrum(d, nperseg, noverlap):
    """
    Power spectrum (scipy.signal.welch)
    Input
    - d: xCDAT variable
    - nperseg: Length of each segment
    - noverlap: Length of overlap between segments
    Output
    - freqs: Sample frequencies
    - psd: Power spectra
    - rn: Rednoise
    - sig95: 95% rednoise confidence level
    """
    # Fill missing date using interpolation
    dnp = np.array(d)
    dfm = np.zeros((d.shape[0], d.shape[1], d.shape[2]), dtype=float)
    for iy in range(d.shape[1]):
        for ix in range(d.shape[2]):
            yp = pd.Series(dnp[:, iy, ix])
            ypfm = yp.interpolate(method="linear")
            dfm[:, iy, ix] = np.array(ypfm)

    # Calculate power spectrum
    freqs, psd = signal.welch(
        dfm, scaling="spectrum", nperseg=nperseg, noverlap=noverlap, axis=0
    )

    # Signigicance test of power spectra (from J. Lee's MOV code)
    nps = max(
        np.floor(((dfm.shape[0] - nperseg) / (nperseg - noverlap)) + 1), 1
    )  # Number of power spectra
    rn = np.zeros((psd.shape[0], psd.shape[1], psd.shape[2]), np.float64)
    sig95 = np.zeros((psd.shape[0], psd.shape[1], psd.shape[2]), np.float64)
    for iy in range(psd.shape[1]):
        for ix in range(psd.shape[2]):
            r1 = np.array(lag1_autocorrelation(dfm[:, iy, ix]))
            rn[:, iy, ix] = rednoise(psd[:, iy, ix], len(freqs), r1)
            nu = 2 * nps
            sig95[:, iy, ix] = RedNoiseSignificanceLevel(nu, rn[:, iy, ix])

    # Decorate arrays with dimensions
    # axisfrq = np.arange(len(freqs))
    axisfrq = range(len(freqs))
    coords=[axisfrq, d.coords[d.dims[1]], d.coords[d.dims[2]]]
    dims=["frequency", d.dims[1], d.dims[2]]   
    freqs = xr.DataArray(freqs, coords=[axisfrq], dims=["frequency"], name="freqs")
    psd = xr.DataArray(psd, coords=coords, dims=dims, name="power")
    rn = xr.DataArray(rn, coords=coords, dims=dims, name="rednoise")
    sig95 = xr.DataArray(sig95, coords=coords, dims=dims, name="sig95")
    
    print("Complete power spectra (segment: ", nperseg, " nps:", nps, ")")
    return freqs, psd, rn, sig95


# ==================================================================================
def lag1_autocorrelation(x):
    lag = 1
    result = float(np.corrcoef(x[:-lag], x[lag:])[0,1])
    return result


# ==================================================================================
def rednoise(VAR, NUMHAR, R1):
    """
    NOTE: THIS PROGRAM IS USED TO CALCULATE THE RED NOISE SPECTRUM OF
          AN INPUT SPECTRUM. Modified from K. Sperber's FORTRAN code.
    Input
    - VAR    : array of spectral estimates (input)
    - NUMHAR : number of harmonics (input)
    - R1     : lag correlation coefficient (input)
    Output
    - RN     : array of null rednoise estimates (output)
    """
    WHITENOISE = sum(VAR) / float(NUMHAR)
    # CALCULATE "NULL" RED NOISE
    R1X2 = 2.0 * R1
    R12 = R1 * R1
    TOP = 1.0 - R12
    BOT = 1.0 + R12
    RN = []
    for K in range(NUMHAR):
        RN.append(
            WHITENOISE * (TOP / (BOT - R1X2 * float(math.cos(math.pi * K / NUMHAR))))
        )
    return RN


# ==================================================================================
def RedNoiseSignificanceLevel(nu, rn, p=0.050):
    """
    nu is the number of degrees of freedom (2 in case of an fft).
    Note: As per Wilks (1995, p. 351, Section 8.5.4) when calculating
    the mean of M spectra and rednoise estimates nu will be nu*M (input)

    factor is the scale factor by which the rednoise must be multiplied by to
    obtain the 95% rednoise confidence level (output)
    Note: the returned value is the reduced chi-square value

    95% Confidence CHI-SQUARED FOR NU DEGREES OF FREEDOM
    """
    factor = chi2.isf(p, nu) / nu
    siglevel = np.multiply(rn, factor)
    return siglevel


# ==================================================================================
def Avg_PS_DomFrq(d, frequency, ntd, dat, mip, frc):
    """
    Domain and Frequency average of spectral power
    Input
    - d: spectral power with lon, lat, and frequency dimensions (xCDAT)
    - ntd: number of time steps per day (daily: 1, 3-hourly: 8)
    - frequency: frequency
    - dat: model name
    - mip: mip name
    - frc: forced or unforced
    Output
    - psdmfm: Domain and Frequency averaged of spectral power (json)
    """
    domains = [
        "Total_50S50N",
        "Ocean_50S50N",
        "Land_50S50N",
        "Total_30N50N",
        "Ocean_30N50N",
        "Land_30N50N",
        "Total_30S30N",
        "Ocean_30S30N",
        "Land_30S30N",
        "Total_50S30S",
        "Ocean_50S30S",
        "Land_50S30S",
    ]

    if ntd == 8:  # 3-hourly data
        frqs_forced = ["semi-diurnal", "diurnal", "semi-annual", "annual"]
        frqs_unforced = [
            "sub-daily",
            "synoptic",
            "sub-seasonal",
            "seasonal-annual",
            "interannual",
        ]
    elif ntd == 1:  # daily data
        frqs_forced = ["semi-annual", "annual"]
        frqs_unforced = ["synoptic", "sub-seasonal", "seasonal-annual", "interannual"]
    else:
        sys.exit("ERROR: ntd " + ntd + " is not defined!")

    if frc == "forced":
        frqs = frqs_forced
    elif frc == "unforced":
        frqs = frqs_unforced
    else:
        sys.exit("ERROR: frc " + frc + " is not defined!")

    d_cdms = xr.DataArray.to_cdms2(d[0])
    mask = cdutil.generateLandSeaMask(d_cdms)
    mask = xr.DataArray.from_cdms2(mask)
    
    psdmfm = {}
    for dom in domains:
        psdmfm[dom] = {}

        if "Ocean" in dom:
            dmask = d.where(mask==0)
        elif "Land" in dom:
            dmask = d.where(mask==1)
        else:
            dmask = d

        dmask = dmask.to_dataset(name="ps")
        dmask = dmask.bounds.add_bounds(axis="X", width=0.5)
        dmask = dmask.bounds.add_bounds(axis="Y", width=0.5)
            
        if "50S50N" in dom:
            am = dmask.sel(lat=slice(-50, 50)).spatial.average("ps", axis=["X", "Y"], weights='generate')["ps"]
        if "30N50N" in dom:
            am = dmask.sel(lat=slice(30, 50)).spatial.average("ps", axis=["X", "Y"], weights='generate')["ps"]
        if "30S30N" in dom:
            am = dmask.sel(lat=slice(-30, 30)).spatial.average("ps", axis=["X", "Y"], weights='generate')["ps"]
        if "50S30S" in dom:
            am = dmask.sel(lat=slice(-50, -30)).spatial.average("ps", axis=["X", "Y"], weights='generate')["ps"]
        am = np.array(am)

        for frq in frqs:
            if frq == "semi-diurnal":  # pr=0.5day
                idx = prdday_to_frqidx(0.5, frequency, ntd)
                amfm = am[idx]
            elif frq == "diurnal":  # pr=1day
                idx = prdday_to_frqidx(1, frequency, ntd)
                amfm = am[idx]
            elif frq == "semi-annual":  # 180day=<pr=<183day
                idx2 = prdday_to_frqidx(180, frequency, ntd)
                idx1 = prdday_to_frqidx(183, frequency, ntd)
                amfm = np.amax(am[idx1 : idx2 + 1])
            elif frq == "annual":  # 360day=<pr=<366day
                idx2 = prdday_to_frqidx(360, frequency, ntd)
                idx1 = prdday_to_frqidx(366, frequency, ntd)
                amfm = np.amax(am[idx1 : idx2 + 1])
            elif frq == "sub-daily":  # pr<1day
                idx1 = prdday_to_frqidx(1, frequency, ntd)
                amfm = np.nanmean(am[idx1 + 1 :])
            elif frq == "synoptic":  # 1day=<pr<20day
                idx2 = prdday_to_frqidx(1, frequency, ntd)
                idx1 = prdday_to_frqidx(20, frequency, ntd)
                amfm = np.nanmean(am[idx1 + 1 : idx2 + 1])
            elif frq == "sub-seasonal":  # 20day=<pr<90day
                idx2 = prdday_to_frqidx(20, frequency, ntd)
                idx1 = prdday_to_frqidx(90, frequency, ntd)
                amfm = np.nanmean(am[idx1 + 1 : idx2 + 1])
            elif frq == "seasonal-annual":  # 90day=<pr<365day
                idx2 = prdday_to_frqidx(90, frequency, ntd)
                idx1 = prdday_to_frqidx(365, frequency, ntd)
                amfm = np.nanmean(am[idx1 + 1 : idx2 + 1])
            elif frq == "interannual":  # 365day=<pr
                idx2 = prdday_to_frqidx(365, frequency, ntd)
                amfm = np.nanmean(am[: idx2 + 1])
            psdmfm[dom][frq] = amfm.tolist()

    print("Complete domain and frequency average of spectral power")
    return psdmfm


# ==================================================================================
def prdday_to_frqidx(prdday, frequency, ntd):
    """
    Find frequency index from input period
    Input
    - prdday: period (day)
    - frequency: frequency
    - ntd: number of time steps per day (daily: 1, 3-hourly: 8)
    Output
    - idx: frequency index
    """
    frq = 1.0 / (float(prdday) * ntd)
    idx = (np.abs(frequency - frq)).argmin()
    return int(idx)
