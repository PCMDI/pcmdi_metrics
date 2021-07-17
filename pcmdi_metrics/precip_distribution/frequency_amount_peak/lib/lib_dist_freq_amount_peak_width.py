import cdms2 as cdms
import MV2 as MV
import cdutil
import genutil
import numpy as np
from regrid2 import Horizontal
import sys


# ==================================================================================
def Regrid2deg(d):
    """
    Regrid to 2deg (180lon*90lat) horizontal resolution
    Input
    - d: cdms variable
    Output
    - drg: cdms variable with 2deg horizontal resolution
    """
    # Regridding
    tgrid = cdms.createUniformGrid(-89, 90, 2.0, 0, 180, 2.0, order="yx")
    orig_grid = d.getGrid()
    regridFunc = Horizontal(orig_grid, tgrid)
    drg = MV.zeros((d.shape[0], tgrid.shape[0], tgrid.shape[1]), MV.float)
    for it in range(d.shape[0]):
        drg[it] = regridFunc(d[it])

    # Dimension information
    time = d.getTime()
    lat = tgrid.getLatitude()
    lon = tgrid.getLongitude()
    drg.setAxisList((time, lat, lon))

    # Missing value (In case, missing value is changed after regridding)
    if d.missing_value > 0:
        drg[drg >= d.missing_value] = d.missing_value
    else:
        drg[drg <= d.missing_value] = d.missing_value
    mask = np.array(drg == d.missing_value)
    drg.mask = mask

    print("Complete regridding from", d.shape, "to", drg.shape)
    return drg


# ==================================================================================
def getDailyCalendarMonth(d, mon):
    """
    Month separation from daily data
    Input
    - d: cdms variable
    - mon: month (e.g., 'JAN', 'FEB', 'MAR', ...)
    Output
    - drg: cdms variable with 2deg horizontal resolution
    """
    a = d.getTime()
    a.designateTime()
    cdutil.setTimeBoundsDaily(a)
    indices, bounds, starts = cdutil.monthBasedSlicer(a, [mon, ])
    calmo = None
    b = MV.ones(a.shape)
    b.setAxis(0, a)
    for i, sub in enumerate(indices):
        tmp = d(time=slice(sub[0], sub[-1]+1))
        if calmo is None:
            calmo = tmp
        else:
            calmo = MV.concatenate((calmo, tmp), axis=2)
    return calmo


# ==================================================================================
def CalcBinStructure(pdata1, bincrates):
    sp1 = pdata1.shape
    L = 2.5e6  # % w/m2. latent heat of vaporization of water
    wm2tommd = 1./L*3600*24  # % conversion from w/m2 to mm/d
    pmax = pdata1.max()/wm2tommd
    maxp = 1500  # % choose an arbitrary upper bound for initial distribution, in w/m2
    # % arbitrary lower bound, in w/m2. Make sure to set this low enough that you catch most of the rain.
    minp = 1
    # %%% thoughts: it might be better to specify the minimum threshold and the
    # %%% bin spacing, which I have around 7%. The goals are to capture as much
    # %%% of the distribution as possible and to balance sampling against
    # %%% resolution. Capturing the upper end is easy: just extend the bins to
    # %%% include the heaviest precipitation event in the dataset. The lower end
    # %%% is harder: it can go all the way to machine epsilon, and there is no
    # %%% obvious reasonable threshold for "rain" over a large spatial scale. The
    # %%% value I chose here captures 97% of rainfall in CMIP5.
    nbins = 100
    binrlog = np.linspace(np.log(minp), np.log(maxp), nbins)
    dbinlog = np.diff(binrlog)
    binllog = binrlog-dbinlog[0]
    binr = np.exp(binrlog)/L*3600*24
    binl = np.exp(binllog)/L*3600*24
    dbin = dbinlog[0]
    binrlogex = binrlog
    binrend = np.exp(binrlogex[len(binrlogex)-1])
    # % extend the bins until the maximum precip anywhere in the dataset falls
    # % within the bins
    # switch maxp to pmax if you want it to depend on your data
    while maxp > binr[len(binr)-1]:
        binrlogex = np.append(binrlogex, binrlogex[len(binrlogex)-1]+dbin)
        binrend = np.exp(binrlogex[len(binrlogex)-1])
        binrlog = binrlogex
        binllog = binrlog-dbinlog[0]
        # %% this is what we'll use to make distributions
        binl = np.exp(binllog)/L*3600*24
        binr = np.exp(binrlog)/L*3600*24
    bincrates = np.append(0, (binl+binr)/2)  # % we'll use this for plotting.

    return binl, binr, bincrates


# ==================================================================================
def MakeDists(pdata, binl):
    # This is called from within makeraindist.
    # Caclulate distributions
    pds = pdata.shape
    nlat = pds[1]
    nlon = pds[2]
    nd = pds[0]
    bins = np.append(0, binl)
    n = np.empty((nlat, nlon, len(binl)))
    binno = np.empty(pdata.shape)
    for ilon in range(nlon):
        for ilat in range(nlat):
            # this is the histogram - we'll get frequency from this
            thisn, thisbin = np.histogram(pdata[:, ilat, ilon], bins)
            n[ilat, ilon, :] = thisn
            # these are the bin locations. we'll use these for the amount dist
            binno[ilat, ilon, :] = np.digitize(pdata[:, ilat, ilon], bins)
    # Calculate the number of days with non-missing data, for normalization
    ndmat = np.tile(np.expand_dims(
        np.nansum(n, axis=2), axis=2), (1, 1, len(bins)-1))
    thisppdfmap = n/ndmat
    # Iterate back over the bins and add up all the precip - this will be the rain amount distribution.
    # This step is probably the limiting factor and might be able to be made more efficient - I had a clever trick in matlab, but it doesn't work in python
    testpamtmap = np.empty(thisppdfmap.shape)
    for ibin in range(len(bins)-1):
        testpamtmap[:, :, ibin] = (pdata*(ibin == binno)).sum(axis=2)
    thispamtmap = testpamtmap/ndmat
    return thisppdfmap, thispamtmap


# ==================================================================================
def CalcRainMetrics(pdistin, bincrates):
    # This calculation can be applied to rain amount or rain frequency distributions
    # Here we'll do it for a distribution averaged over a region, but you could also do it at each grid point
    pdist = np.copy(pdistin)
    # this is the threshold, 10% of rain amount or rain frequency
    tile = np.array(0.1)
    # If this is frequency, get rid of the dry frequency. If it's amount, it should already be zero or close to it.
    pdist[0] = 0
    pmax = pdist.max()
    if pmax > 0:
        imax = np.nonzero(pdist == pmax)
        rmax = np.interp(imax, range(0, len(bincrates)), bincrates)
        rainpeak = rmax[0][0]
        # we're going to find the width by summing downward from pmax to lines at different heights, and then interpolating to figure out the rain rates that intersect the line.
        theps = np.linspace(0.1, .99, 99)*pmax
        thefrac = np.empty(theps.shape)
        for i in range(len(theps)):
            thisp = theps[i]
            overp = (pdist-thisp)*(pdist > thisp)
            thefrac[i] = sum(overp)/sum(pdist)
        ptilerain = np.interp(-tile, -thefrac, theps)
        # ptilerain/db ### check this against rain amount plot
        # ptilerain*100/db ### check this against rain frequency plot
        diffraintile = (pdist-ptilerain)
        alli = np.nonzero(diffraintile > 0)
        afterfirst = alli[0][0]
        noistart = np.nonzero(diffraintile[0:afterfirst] < 0)
        beforefirst = noistart[0][len(noistart[0])-1]
        incinds = range(beforefirst, afterfirst+1)
        # need error handling on these for when inter doesn't behave well and there are multiple crossings
        if np.all(np.diff(diffraintile[incinds]) > 0):
            # this is ideally what happens. note: r1 is a bin index, not a rain rate.
            r1 = np.interp(0, diffraintile[incinds], incinds)
        else:
            # in case interp won't return something meaningful, we use this kluge.
            r1 = np.average(incinds)
        beforelast = alli[0][len(alli[0])-1]
        noiend = np.nonzero(diffraintile[beforelast:(
            len(diffraintile)-1)] < 0)+beforelast
        afterlast = noiend[0][0]
        decinds = range(beforelast, afterlast+1)
        if np.all(np.diff(-diffraintile[decinds]) > 0):
            r2 = np.interp(0, -diffraintile[decinds], decinds)
        else:
            r2 = np.average(decinds)
        # Bin width - needed to normalize the rain amount distribution
        db = (bincrates[2]-bincrates[1])/bincrates[1]
        rainwidth = (r2-r1)*db+1
        return rainpeak, rainwidth, (imax[0][0], pmax), (r1, r2, ptilerain)
    else:
        return 0, 0, (0, pmax), (0, 0, 0)


# ==================================================================================
def AvgDomain(d):
    """
    Domain average
    Input
    - d: cdms variable
    Output
    - ddom: Domain averaged of data (json)
    """
    domains = ["Total_50S50N", "Ocean_50S50N", "Land_50S50N",
               "Total_30N50N", "Ocean_30N50N", "Land_30N50N",
               "Total_30S30N", "Ocean_30S30N", "Land_30S30N",
               "Total_50S30S", "Ocean_50S30S", "Land_50S30S"]

    mask = cdutil.generateLandSeaMask(d[0])
    d, mask2 = genutil.grower(d, mask)
    d_ocean = MV.masked_where(mask2 == 1.0, d)
    d_land = MV.masked_where(mask2 == 0.0, d)

    ddom = {}
    for dom in domains:

        if "Ocean" in dom:
            dmask = d_ocean
        elif "Land" in dom:
            dmask = d_land
        else:
            dmask = d

        if "50S50N" in dom:
            am = cdutil.averager(
                dmask(latitude=(-50, 50)), axis="xy")
        if "30N50N" in dom:
            am = cdutil.averager(
                dmask(latitude=(30, 50)), axis="xy")
        if "30S30N" in dom:
            am = cdutil.averager(
                dmask(latitude=(-30, 30)), axis="xy")
        if "50S30S" in dom:
            am = cdutil.averager(
                dmask(latitude=(-50, -30)), axis="xy")

        ddom[dom] = am.tolist()

    print("Complete domain average")
    return ddom
