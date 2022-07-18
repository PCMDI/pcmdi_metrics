import cdms2 as cdms
import MV2 as MV
import cdutil
import genutil
import numpy as np
import glob
import copy
import pcmdi_metrics
import regionmask
import rasterio.features
import xarray as xr
from regrid2 import Horizontal
from shapely.geometry import Polygon, MultiPolygon
import sys
import os


# ==================================================================================
def precip_distribution_frq_amt (dat, drg, syr, eyr, res, outdir, ref, refdir, cmec):
    """
    - The metric algorithm is based on Dr. Pendergrass's work (https://github.com/apendergrass/rain-metrics-python)
    - Pre-processing and post-processing of data are modified for PMP as below:
      Regridding (in driver code) -> Month separation -> Distributions -> Domain average -> Metrics -> Write
    """

    # Month separation
    months = ['ANN', 'MAM', 'JJA', 'SON', 'DJF',
              'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    pdfpeakmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    pdfwidthmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    amtpeakmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    amtwidthmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    for im, mon in enumerate(months):

        if mon == 'ANN':
            dmon = drg
        elif mon == 'MAM':
            dmon = getDailyCalendarMonth(drg, ['MAR', 'APR', 'MAY'])
        elif mon == 'JJA':
            dmon = getDailyCalendarMonth(drg, ['JUN', 'JUL', 'AUG'])
        elif mon == 'SON':
            dmon = getDailyCalendarMonth(drg, ['SEP', 'OCT', 'NOV'])
        elif mon == 'DJF':
            # dmon = getDailyCalendarMonth(drg, ['DEC','JAN','FEB'])
            dmon = getDailyCalendarMonth(drg(
                time=(str(syr)+"-3-1 0:0:0", str(eyr)+"-11-30 23:59:59")), ['DEC', 'JAN', 'FEB'])
        else:
            dmon = getDailyCalendarMonth(drg, mon)

        print(dat, mon, dmon.shape)

        pdata1 = dmon

        # Calculate bin structure
        binl, binr, bincrates = CalcBinStructure(pdata1)

        # Calculate distributions at each grid point
        ppdfmap, pamtmap, bins, ppdfmap_tn = MakeDists(pdata1, binl)

        # Calculate metrics from the distribution at each grid point
        for i in range(drg.shape[2]):
            for j in range(drg.shape[1]):
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    ppdfmap[:, j, i], bincrates)
                pdfpeakmap[im, j, i] = rainpeak
                pdfwidthmap[im, j, i] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pamtmap[:, j, i], bincrates)
                amtpeakmap[im, j, i] = rainpeak
                amtwidthmap[im, j, i] = rainwidth

    # Make Spatial pattern of distributions with separated months
        if im == 0:
            pdfmapmon = np.expand_dims(ppdfmap, axis=0)
            pdfmapmon_tn = np.expand_dims(ppdfmap_tn, axis=0)
            amtmapmon = np.expand_dims(pamtmap, axis=0)
        else:
            pdfmapmon = MV.concatenate(
                (pdfmapmon, np.expand_dims(ppdfmap, axis=0)), axis=0)
            pdfmapmon_tn = MV.concatenate(
                (pdfmapmon_tn, np.expand_dims(ppdfmap_tn, axis=0)), axis=0)
            amtmapmon = MV.concatenate(
                (amtmapmon, np.expand_dims(pamtmap, axis=0)), axis=0)

    axmon = cdms.createAxis(range(len(months)), id='month')
    axbin = cdms.createAxis(range(len(binl)), id='bin')
    lat = drg.getLatitude()
    lon = drg.getLongitude()

    pdfmapmon.setAxisList((axmon, axbin, lat, lon))
    pdfmapmon_tn.setAxisList((axmon, axbin, lat, lon))
    amtmapmon.setAxisList((axmon, axbin, lat, lon))

    pdfpeakmap = MV.array(pdfpeakmap)
    pdfwidthmap = MV.array(pdfwidthmap)
    amtpeakmap = MV.array(amtpeakmap)
    amtwidthmap = MV.array(amtwidthmap)
    pdfpeakmap.setAxisList((axmon, lat, lon))
    pdfwidthmap.setAxisList((axmon, lat, lon))
    amtpeakmap.setAxisList((axmon, lat, lon))
    amtwidthmap.setAxisList((axmon, lat, lon))

    res_nxny=str(int(360/res[0]))+"x"+str(int(180/res[1]))

    # Write data (nc file for spatial pattern of distributions)
    outfilename = "dist_frq.amt_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfmapmon, id="pdf")
        out.write(pdfmapmon_tn, id="pdf_tn")
        out.write(amtmapmon, id="amt")
        out.write(bins, id="binbounds")

    # Write data (nc file for spatial pattern of metrics)
    outfilename = "dist_frq.amt_metrics_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfpeakmap, id="frqpeak")
        out.write(pdfwidthmap, id="frqwidth")
        out.write(amtpeakmap, id="amtpeak")
        out.write(amtwidthmap, id="amtwidth")

    # Calculate metrics from the distribution at each domain
    metricsdom = {'RESULTS': {dat: {}}}
    metricsdom3C = {'RESULTS': {dat: {}}}
    metricsdomAR6 = {'RESULTS': {dat: {}}}
    metricsdom['RESULTS'][dat], pdfdom, amtdom = CalcMetricsDomain(pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir)
    metricsdom3C['RESULTS'][dat], pdfdom3C, amtdom3C = CalcMetricsDomain3Clust(pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir)
    metricsdomAR6['RESULTS'][dat], pdfdomAR6, amtdomAR6 = CalcMetricsDomainAR6(pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir)

    # Write data (nc file for distributions at each domain)
    outfilename = "dist_frq.amt_domain_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfdom, id="pdf")
        out.write(amtdom, id="amt")
        out.write(bins, id="binbounds")

    # Write data (nc file for distributions at each domain with 3 clustering regions)
    outfilename = "dist_frq.amt_domain3C_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfdom3C, id="pdf")
        out.write(amtdom3C, id="amt")
        out.write(bins, id="binbounds")

    # Write data (nc file for distributions at each domain with AR6 regions)
    outfilename = "dist_frq.amt_domainAR6_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfdomAR6, id="pdf")
        out.write(amtdomAR6, id="amt")
        out.write(bins, id="binbounds")


    # Write data (json file for domain metrics)
    outfilename = "dist_frq.amt_metrics_domain_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metricsdom,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))

    # Write data (json file for domain metrics with 3 clustering regions)
    outfilename = "dist_frq.amt_metrics_domain3C_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metricsdom3C,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))

    # Write data (json file for domain metrics with AR6 regions)
    outfilename = "dist_frq.amt_metrics_domainAR6_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metricsdomAR6,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))

    print("Completed metrics from precipitation frequency and amount distributions")


# ==================================================================================
def precip_distribution_cum (dat, drg, cal, syr, eyr, res, outdir, cmec):
    """
    - The metric algorithm is based on Dr. Pendergrass's work (https://github.com/apendergrass/unevenprecip)
    - Pre-processing and post-processing of data are modified for PMP as below:
      Regridding (in driver code) -> Month separation -> Year separation -> Unevenness and other metrics -> Year median -> Domain median -> Write
    """

    missingthresh = 0.3  # threshold of missing data fraction at which a year is thrown out

    # Month separation
    months = ['ANN', 'MAM', 'JJA', 'SON', 'DJF',
              'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    if "360" in cal:
        ndymon = [360, 90, 90, 90, 90,
                  30, 30, 30, 30, 30, 30,
                  30, 30, 30, 30, 30, 30]
        ldy = 30
    else:
        # Only considered 365-day calendar becauase, in cumulative distribution as a function of the wettest days, the last part of the distribution is not affect to metrics.
        ndymon = [365, 92, 92, 91, 90,
                  31, 28, 31, 30, 31, 30,
                  31, 31, 30, 31, 30, 31]
        ldy = 31

    res_nxny=str(int(360/res[0]))+"x"+str(int(180/res[1]))

    # Open nc file for writing data of spatial pattern of cumulated fractions with separated month
    outfilename = "dist_cumfrac_regrid." + \
        res_nxny+"_" + dat + ".nc"
    outcumfrac = cdms.open(os.path.join(
        outdir(output_type='diagnostic_results'), outfilename), "w")

    for im, mon in enumerate(months):

        if mon == 'ANN':
            dmon = drg
        elif mon == 'MAM':
            dmon = getDailyCalendarMonth(drg, ['MAR', 'APR', 'MAY'])
        elif mon == 'JJA':
            dmon = getDailyCalendarMonth(drg, ['JUN', 'JUL', 'AUG'])
        elif mon == 'SON':
            dmon = getDailyCalendarMonth(drg, ['SEP', 'OCT', 'NOV'])
        elif mon == 'DJF':
            # dmon = getDailyCalendarMonth(drg, ['DEC','JAN','FEB'])
            dmon = getDailyCalendarMonth(drg(
                time=(str(syr)+"-3-1 0:0:0", str(eyr)+"-11-30 23:59:59")), ['DEC', 'JAN', 'FEB'])
        else:
            dmon = getDailyCalendarMonth(drg, mon)

        print(dat, mon, dmon.shape)

        # Calculate unevenness
        nyr = eyr-syr+1
        if mon == 'DJF':
            nyr = nyr - 1
        cfy = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        prdyfracyr = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        sdiiyr = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        pfracyr = np.full(
            (nyr, ndymon[im], dmon.shape[1], dmon.shape[2]), np.nan)

        for iyr, year in enumerate(range(syr, eyr + 1)):
            if mon == 'DJF':
                if year == eyr:
                    thisyear = None
                else:
                    thisyear = dmon(time=(str(year) + "-12-1 0:0:0",
                                          str(year+1) + "-3-1 23:59:59"))
            else:
                thisyear = dmon(time=(str(year) + "-1-1 0:0:0",
                                      str(year) + "-12-" + str(ldy) + " 23:59:59"))

            if thisyear is not None:
                print(year, thisyear.shape)
                pfrac, ndhy, prdyfrac, sdii = oneyear(thisyear, missingthresh)
                cfy[iyr, :, :] = ndhy
                prdyfracyr[iyr, :, :] = prdyfrac
                sdiiyr[iyr, :, :] = sdii
                pfracyr[iyr, :, :, :] = pfrac[:ndymon[im], :, :]
                print(year, 'pfrac.shape is ', pfrac.shape, ', but',
                      pfrac[:ndymon[im], :, :].shape, ' is used')

        ndm = np.nanmedian(cfy, axis=0)  # ignore years with zero precip
        missingfrac = (np.sum(np.isnan(cfy), axis=0)/nyr)
        ndm[np.where(missingfrac > missingthresh)] = np.nan
        prdyfracm = np.nanmedian(prdyfracyr, axis=0)
        sdiim = np.nanmedian(sdiiyr, axis=0)

        pfracm = np.nanmedian(pfracyr, axis=0)
        axbin = cdms.createAxis(range(1, ndymon[im]+1), id='cumday')
        lat = dmon.getLatitude()
        lon = dmon.getLongitude()
        pfracm = MV.array(pfracm)
        pfracm.setAxisList((axbin, lat, lon))
        outcumfrac.write(pfracm, id="cumfrac_"+mon)

    # Make Spatial pattern with separated months
        if im == 0:
            ndmmon = np.expand_dims(ndm, axis=0)
            prdyfracmmon = np.expand_dims(prdyfracm, axis=0)
            sdiimmon = np.expand_dims(sdiim, axis=0)
        else:
            ndmmon = MV.concatenate(
                (ndmmon, np.expand_dims(ndm, axis=0)), axis=0)
            prdyfracmmon = MV.concatenate(
                (prdyfracmmon, np.expand_dims(prdyfracm, axis=0)), axis=0)
            sdiimmon = MV.concatenate(
                (sdiimmon, np.expand_dims(sdiim, axis=0)), axis=0)

    # Domain median
    axmon = cdms.createAxis(range(len(months)), id='time')
    ndmmon = MV.array(ndmmon)
    ndmmon.setAxisList((axmon, lat, lon))
    prdyfracmmon = MV.array(prdyfracmmon)
    prdyfracmmon.setAxisList((axmon, lat, lon))
    sdiimmon = MV.array(sdiimmon)
    sdiimmon.setAxisList((axmon, lat, lon))

    metrics = {'RESULTS': {dat: {}}}
    metrics['RESULTS'][dat]['unevenness'] = MedDomain(ndmmon, months)
    metrics['RESULTS'][dat]['prdyfrac'] = MedDomain(prdyfracmmon, months)
    metrics['RESULTS'][dat]['sdii'] = MedDomain(sdiimmon, months)

    metrics3C = {'RESULTS': {dat: {}}}
    metrics3C['RESULTS'][dat]['unevenness'] = MedDomain3Clust(ndmmon, months)
    metrics3C['RESULTS'][dat]['prdyfrac'] = MedDomain3Clust(prdyfracmmon, months)
    metrics3C['RESULTS'][dat]['sdii'] = MedDomain3Clust(sdiimmon, months)

    metricsAR6 = {'RESULTS': {dat: {}}}
    metricsAR6['RESULTS'][dat]['unevenness'] = MedDomainAR6(ndmmon, months)
    metricsAR6['RESULTS'][dat]['prdyfrac'] = MedDomainAR6(prdyfracmmon, months)
    metricsAR6['RESULTS'][dat]['sdii'] = MedDomainAR6(sdiimmon, months)

    axmon = cdms.createAxis(range(len(months)), id='month')
    ndmmon.setAxisList((axmon, lat, lon))
    prdyfracmmon.setAxisList((axmon, lat, lon))
    sdiimmon.setAxisList((axmon, lat, lon))

    # Write data (nc file for spatial pattern of metrics)
    outfilename = "dist_cumfrac_metrics_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(ndmmon, id="unevenness")
        out.write(prdyfracmmon, id="prdyfrac")
        out.write(sdiimmon, id="sdii")

    # Write data (json file for domain median metrics)
    outfilename = "dist_cumfrac_metrics_domain.median_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metrics,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))

    # Write data (json file for domain median metrics with 3 clustering regions)
    outfilename = "dist_cumfrac_metrics_domain.median.3C_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metrics3C,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))

    # Write data (json file for domain median metrics with AR6 regions)
    outfilename = "dist_cumfrac_metrics_domain.median.AR6_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metricsAR6,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))

    print("Completed metrics from precipitation cumulative distributions")


# ==================================================================================
def Regrid(d, resdeg):
    """
    Regridding horizontal resolution
    Input
    - d: cdms variable
    - resdeg: list of target horizontal resolution [degree] for lon and lat (e.g., [4, 4])
    Output
    - drg: cdms variable with target horizontal resolution
    """
    # Regridding
    nx = 360/resdeg[0]
    ny = 180/resdeg[1]
    sy = -90 + resdeg[1]/2
    tgrid = cdms.createUniformGrid(
        sy, ny, resdeg[1], 0, nx, resdeg[0], order="yx")
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

    print("Completed regridding from", d.shape, "to", drg.shape)
    return drg


# ==================================================================================
def getDailyCalendarMonth(d, mon):
    """
    Month separation from daily data
    Input
    - d: cdms variable
    - mon: list of months (e.g., ['JAN'], ['FEB'], ['MAR','APR','MAY'], ...)
    Output
    - calmo: cdms variable concatenated for specific month
    """
    a = d.getTime()
    cdutil.setTimeBoundsDaily(a)
    indices, bounds, starts = cdutil.monthBasedSlicer(a, mon)
    calmo = None
    b = MV.ones(a.shape)
    b.setAxis(0, a)
    for i, sub in enumerate(indices):
        tmp = d(time=slice(sub[0], sub[-1]+1))
        if calmo is None:
            calmo = tmp
        else:
            calmo = MV.concatenate((calmo, tmp), axis=0)
    return calmo


# ==================================================================================
def CalcBinStructure(pdata1):
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

    axbin = cdms.createAxis(range(len(binl)), id='bin')
    binl = MV.array(binl)
    binr = MV.array(binr)
    binl.setAxis(0, axbin)
    binr.setAxis(0, axbin)

    return binl, binr, bincrates


# ==================================================================================
def MakeDists(pdata, binl):
    # This is called from within makeraindist.
    # Caclulate distributions
    nlat = pdata.shape[1]
    nlon = pdata.shape[2]
    nd = pdata.shape[0]
    bins = np.append(0, binl)
    n = np.empty((len(binl), nlat, nlon))
    binno = np.empty(pdata.shape)
    for ilon in range(nlon):
        for ilat in range(nlat):
            # this is the histogram - we'll get frequency from this
            thisn, thisbin = np.histogram(pdata[:, ilat, ilon], bins)
            # n[:, ilat, ilon] = thisn
            thmiss=0.7 # threshold for missing grid
            if np.sum(thisn)>=nd*thmiss:
                n[:, ilat, ilon] = thisn
            else:
                n[:, ilat, ilon] = np.nan

            # these are the bin locations. we'll use these for the amount dist
            binno[:, ilat, ilon] = np.digitize(pdata[:, ilat, ilon], bins)
    # Calculate the number of days with non-missing data, for normalization
    ndmat = np.tile(np.expand_dims(
       # np.nansum(n, axis=0), axis=0), (len(bins)-1, 1, 1))
       np.sum(n, axis=0), axis=0), (len(bins)-1, 1, 1))

    thisppdfmap = n/ndmat
    thisppdfmap_tn = thisppdfmap*ndmat
    # Iterate back over the bins and add up all the precip - this will be the rain amount distribution.
    # This step is probably the limiting factor and might be able to be made more efficient - I had a clever trick in matlab, but it doesn't work in python
    testpamtmap = np.empty(thisppdfmap.shape)
    for ibin in range(len(bins)-1):
        testpamtmap[ibin, :, :] = (pdata*(ibin == binno)).sum(axis=0)
    thispamtmap = testpamtmap/ndmat

    axbin = cdms.createAxis(range(len(binl)), id='bin')
    lat = pdata.getLatitude()
    lon = pdata.getLongitude()
    thisppdfmap = MV.array(thisppdfmap)
    thisppdfmap.setAxisList((axbin, lat, lon))
    thisppdfmap_tn = MV.array(thisppdfmap_tn)
    thisppdfmap_tn.setAxisList((axbin, lat, lon))
    thispamtmap = MV.array(thispamtmap)
    thispamtmap.setAxisList((axbin, lat, lon))

    axbinbound = cdms.createAxis(range(len(thisbin)), id='binbound')
    thisbin = MV.array(thisbin)
    thisbin.setAxis(0, axbinbound)

    return thisppdfmap, thispamtmap, thisbin, thisppdfmap_tn


# ==================================================================================
def CalcRainMetrics(pdistin, bincrates):
    # This calculation can be applied to rain amount or rain frequency distributions
    # Here we'll do it for a distribution averaged over a region, but you could also do it at each grid point
    pdist = np.copy(pdistin)
    # this is the threshold, 10% of rain amount or rain frequency
    tile = np.array(0.1)

    # If this is frequency, get rid of the dry frequency. If it's amount, it should already be zero or close to it. (Pendergrass and Hartmann 2014)
    # pdist[0] = 0
    # msahn, Days with precip<0.1mm/day are considered dry (Pendergrass and Deser 2017)
    thidx=np.argwhere(bincrates>0.1)
    thidx=int(thidx[0][0])
    pdist[:thidx] = 0
    #-----------------------------------------------------

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

        # msahn For treat noiend=[]
        # if bool(noiend.any()) is False:
        if np.array(noiend).size==0:
            rainwidth = 0
            r2 = r1
        else:
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
        # return 0, 0, (0, pmax), (0, 0, 0)
        return np.nan, np.nan, (np.nan, pmax), (np.nan, np.nan, np.nan)


# ==================================================================================
def CalcMetricsDomain(pdf, amt, months, bincrates, dat, ref, ref_dir):
    """
    Input
    - pdf: pdf
    - amt: amount distribution
    - months: month list of input data
    - bincrates: bin centers
    - dat: data name
    - ref: reference data name
    - ref_dir: reference data directory
    Output
    - metrics: metrics for each domain
    - pdfdom: pdf for each domain
    - amtdom: amt for each domain
    """
    domains = ["Total_50S50N", "Ocean_50S50N", "Land_50S50N",
               "Total_30N50N", "Ocean_30N50N", "Land_30N50N",
               "Total_30S30N", "Ocean_30S30N", "Land_30S30N",
               "Total_50S30S", "Ocean_50S30S", "Land_50S30S"]

    ddom = []
    for d in [pdf, amt]:

        mask = cdutil.generateLandSeaMask(d[0,0])
        d, mask2 = genutil.grower(d, mask)
        d_ocean = MV.masked_where(mask2 == 1.0, d)
        d_land = MV.masked_where(mask2 == 0.0, d)

        for dom in domains:

            if "Ocean" in dom:
                dmask = d_ocean
            elif "Land" in dom:
                dmask = d_land
            else:
                dmask = d

            if "50S50N" in dom:
                am = cdutil.averager(dmask(latitude=(-50, 50)), axis="xy")
            if "30N50N" in dom:
                am = cdutil.averager(dmask(latitude=(30, 50)), axis="xy")
            if "30S30N" in dom:
                am = cdutil.averager(dmask(latitude=(-30, 30)), axis="xy")
            if "50S30S" in dom:
                am = cdutil.averager(dmask(latitude=(-50, -30)), axis="xy")

            ddom.append(am)

    ddom = MV.reshape(ddom,(-1,len(domains),am.shape[0],am.shape[1]))
    ddom = np.swapaxes(ddom,1,3)
    ddom = np.swapaxes(ddom,1,2)
    print(ddom.shape)

    pdfdom = ddom[0]
    amtdom = ddom[1]
    axdom = cdms.createAxis(range(len(domains)), id='domains')
    pdfdom.setAxisList((am.getAxis(0),am.getAxis(1),axdom))
    amtdom.setAxisList((am.getAxis(0),am.getAxis(1),axdom))

    if dat == ref:
        pdfdom_ref = pdfdom
        amtdom_ref = amtdom
    else:
        file = 'dist_frq.amt_domain_regrid.'+str(pdf.shape[3])+"x"+str(pdf.shape[2])+'_'+ref+'.nc'
        pdfdom_ref = cdms.open(os.path.join(ref_dir, file))['pdf']
        amtdom_ref = cdms.open(os.path.join(ref_dir, file))['amt']

    metrics={}
    metrics['frqpeak']={}
    metrics['frqwidth']={}
    metrics['amtpeak']={}
    metrics['amtwidth']={}
    metrics['pscore']={}
    metrics['frqP10']={}
    metrics['frqP20']={}
    metrics['frqP80']={}
    metrics['frqP90']={}
    metrics['amtP10']={}
    metrics['amtP20']={}
    metrics['amtP80']={}
    metrics['amtP90']={}
    for idm, dom in enumerate(domains):
        metrics['frqpeak'][dom]={'CalendarMonths':{}}
        metrics['frqwidth'][dom]={'CalendarMonths':{}}
        metrics['amtpeak'][dom]={'CalendarMonths':{}}
        metrics['amtwidth'][dom]={'CalendarMonths':{}}
        metrics['pscore'][dom]={'CalendarMonths':{}}
        metrics['frqP10'][dom]={'CalendarMonths':{}}
        metrics['frqP20'][dom]={'CalendarMonths':{}}
        metrics['frqP80'][dom]={'CalendarMonths':{}}
        metrics['frqP90'][dom]={'CalendarMonths':{}}
        metrics['amtP10'][dom]={'CalendarMonths':{}}
        metrics['amtP20'][dom]={'CalendarMonths':{}}
        metrics['amtP80'][dom]={'CalendarMonths':{}}
        metrics['amtP90'][dom]={'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[im,:,idm], bincrates)
                metrics['frqpeak'][dom][mon] = rainpeak
                metrics['frqwidth'][dom][mon] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[im,:,idm], bincrates)
                metrics['amtpeak'][dom][mon] = rainpeak
                metrics['amtwidth'][dom][mon] = rainwidth
                metrics['pscore'][dom][mon] = CalcPscore(pdfdom[im,:,idm], pdfdom_ref[im,:,idm])

                metrics['frqP10'][dom][mon], metrics['frqP20'][dom][mon], metrics['frqP80'][dom][mon], metrics['frqP90'][dom][mon], metrics['amtP10'][dom][mon], metrics['amtP20'][dom][mon], metrics['amtP80'][dom][mon], metrics['amtP90'][dom][mon] = CalcP10P90(pdfdom[im,:,idm], amtdom[im,:,idm], amtdom_ref[im,:,idm], bincrates)

            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[im,:,idm], bincrates)
                metrics['frqpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['frqwidth'][dom]['CalendarMonths'][imn] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[im,:,idm], bincrates)
                metrics['amtpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['amtwidth'][dom]['CalendarMonths'][imn] = rainwidth
                metrics['pscore'][dom]['CalendarMonths'][imn] = CalcPscore(pdfdom[im,:,idm], pdfdom_ref[im,:,idm])

                metrics['frqP10'][dom]['CalendarMonths'][imn], metrics['frqP20'][dom]['CalendarMonths'][imn], metrics['frqP80'][dom]['CalendarMonths'][imn], metrics['frqP90'][dom]['CalendarMonths'][imn], metrics['amtP10'][dom]['CalendarMonths'][imn], metrics['amtP20'][dom]['CalendarMonths'][imn], metrics['amtP80'][dom]['CalendarMonths'][imn], metrics['amtP90'][dom]['CalendarMonths'][imn] = CalcP10P90(pdfdom[im,:,idm], amtdom[im,:,idm], amtdom_ref[im,:,idm], bincrates)

    print("Completed domain metrics")
    return metrics, pdfdom, amtdom


# ==================================================================================
def CalcMetricsDomain3Clust(pdf, amt, months, bincrates, dat, ref, ref_dir):
    """
    Input
    - pdf: pdf
    - amt: amount distribution
    - months: month list of input data
    - bincrates: bin centers
    - dat: data name
    - ref: reference data name
    - ref_dir: reference data directory
    Output
    - metrics: metrics for each domain
    - pdfdom: pdf for each domain
    - amtdom: amt for each domain
    """
    domains = ["Total_HR_50S50N", "Total_MR_50S50N", "Total_LR_50S50N",
               "Total_HR_30N50N", "Total_MR_30N50N", "Total_LR_30N50N",
               "Total_HR_30S30N", "Total_MR_30S30N", "Total_LR_30S30N",
               "Total_HR_50S30S", "Total_MR_50S30S", "Total_LR_50S30S",
               "Ocean_HR_50S50N", "Ocean_MR_50S50N", "Ocean_LR_50S50N",
               "Ocean_HR_30N50N", "Ocean_MR_30N50N", "Ocean_LR_30N50N",
               "Ocean_HR_30S30N", "Ocean_MR_30S30N", "Ocean_LR_30S30N",
               "Ocean_HR_50S30S", "Ocean_MR_50S30S", "Ocean_LR_50S30S",
               "Land_HR_50S50N", "Land_MR_50S50N", "Land_LR_50S50N",
               "Land_HR_30N50N", "Land_MR_30N50N", "Land_LR_30N50N",
               "Land_HR_30S30N", "Land_MR_30S30N", "Land_LR_30S30N",
               "Land_HR_50S30S", "Land_MR_50S30S", "Land_LR_50S30S"]

    indir = '../lib'
    file = 'cluster3_pdf.amt_regrid.360x180_IMERG_ALL.nc'
    cluster = xr.open_dataset(os.path.join(indir, file))['cluster_nb']

    regs=['HR', 'MR', 'LR']
    mpolygons=[]
    regs_name=[]
    for irg, reg in enumerate(regs):
        if reg=='HR':
            data=xr.where(cluster==0, 1, 0)
            regs_name.append('Heavy precipitating region')
        elif reg=='MR':
            data=xr.where(cluster==1, 1, 0)
            regs_name.append('Moderate precipitating region')
        elif reg=='LR':
            data=xr.where(cluster==2, 1, 0)
            regs_name.append('Light precipitating region')
        else:
            print('ERROR: data is not defined')
            exit()

        shapes = rasterio.features.shapes(np.int32(data))

        polygons=[]
        for ish, shape in enumerate(shapes):
            for idx, xy in enumerate(shape[0]["coordinates"][0]):
                lst = list(xy)
                lst[0] = lst[0]
                lst[1] = lst[1]-89.5
                tup = tuple(lst)
                shape[0]["coordinates"][0][idx]=tup
            if shape[1] == 1:
                polygons.append(Polygon(shape[0]["coordinates"][0]))

        mpolygons.append(MultiPolygon(polygons).simplify(3, preserve_topology=False))

    region = regionmask.Regions(mpolygons, names=regs_name, abbrevs=regs, name="Heavy/Moderate/Light precipitating regions")
    print(region)

    ddom = []
    for d in [pdf, amt]:
        d_xr = xr.DataArray.from_cdms2(d[0,0])
        mask_3D = region.mask_3D(d_xr, lon_name='longitude', lat_name='latitude')
        mask_3D = xr.DataArray.to_cdms2(mask_3D)

        mask = cdutil.generateLandSeaMask(d[0,0])
        mask_3D, mask2 = genutil.grower(mask_3D, mask)
        mask_3D_ocn = MV.where(mask2 == 0.0, mask_3D, False)
        mask_3D_lnd = MV.where(mask2 == 1.0, mask_3D, False)

        for dom in domains:
            if "Ocean" in dom:
                mask_3D_tmp = mask_3D_ocn
            elif "Land" in dom:
                mask_3D_tmp = mask_3D_lnd
            else:
                mask_3D_tmp = mask_3D

            if "HR" in dom:
                d, mask3 = genutil.grower(d, mask_3D_tmp[0,:,:])
            elif "MR" in dom:
                d, mask3 = genutil.grower(d, mask_3D_tmp[1,:,:])
            elif "LR" in dom:
                d, mask3 = genutil.grower(d, mask_3D_tmp[2,:,:])
            else:
                print('ERROR: HR/MR/LR is not defined')
                exit()

            dmask = MV.masked_where(~mask3, d)

            if "50S50N" in dom:
                am = cdutil.averager(dmask(latitude=(-50, 50)), axis="xy")
            if "30N50N" in dom:
                am = cdutil.averager(dmask(latitude=(30, 50)), axis="xy")
            if "30S30N" in dom:
                am = cdutil.averager(dmask(latitude=(-30, 30)), axis="xy")
            if "50S30S" in dom:
                am = cdutil.averager(dmask(latitude=(-50, -30)), axis="xy")

            ddom.append(am)

    ddom = MV.reshape(ddom,(-1,len(domains),am.shape[0],am.shape[1]))
    ddom = np.swapaxes(ddom,1,3)
    ddom = np.swapaxes(ddom,1,2)
    print(ddom.shape)

    pdfdom = ddom[0]
    amtdom = ddom[1]
    axdom = cdms.createAxis(range(len(domains)), id='domains')
    pdfdom.setAxisList((am.getAxis(0),am.getAxis(1),axdom))
    amtdom.setAxisList((am.getAxis(0),am.getAxis(1),axdom))

    if dat == ref:
        pdfdom_ref = pdfdom
        amtdom_ref = amtdom
    else:
        file = 'dist_frq.amt_domain3C_regrid.'+str(pdf.shape[3])+"x"+str(pdf.shape[2])+'_'+ref+'.nc'
        pdfdom_ref = cdms.open(os.path.join(ref_dir, file))['pdf']
        amtdom_ref = cdms.open(os.path.join(ref_dir, file))['amt']

    metrics={}
    metrics['frqpeak']={}
    metrics['frqwidth']={}
    metrics['amtpeak']={}
    metrics['amtwidth']={}
    metrics['pscore']={}
    metrics['frqP10']={}
    metrics['frqP20']={}
    metrics['frqP80']={}
    metrics['frqP90']={}
    metrics['amtP10']={}
    metrics['amtP20']={}
    metrics['amtP80']={}
    metrics['amtP90']={}
    for idm, dom in enumerate(domains):
        metrics['frqpeak'][dom]={'CalendarMonths':{}}
        metrics['frqwidth'][dom]={'CalendarMonths':{}}
        metrics['amtpeak'][dom]={'CalendarMonths':{}}
        metrics['amtwidth'][dom]={'CalendarMonths':{}}
        metrics['pscore'][dom]={'CalendarMonths':{}}
        metrics['frqP10'][dom]={'CalendarMonths':{}}
        metrics['frqP20'][dom]={'CalendarMonths':{}}
        metrics['frqP80'][dom]={'CalendarMonths':{}}
        metrics['frqP90'][dom]={'CalendarMonths':{}}
        metrics['amtP10'][dom]={'CalendarMonths':{}}
        metrics['amtP20'][dom]={'CalendarMonths':{}}
        metrics['amtP80'][dom]={'CalendarMonths':{}}
        metrics['amtP90'][dom]={'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[im,:,idm], bincrates)
                metrics['frqpeak'][dom][mon] = rainpeak
                metrics['frqwidth'][dom][mon] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[im,:,idm], bincrates)
                metrics['amtpeak'][dom][mon] = rainpeak
                metrics['amtwidth'][dom][mon] = rainwidth
                metrics['pscore'][dom][mon] = CalcPscore(pdfdom[im,:,idm], pdfdom_ref[im,:,idm])

                metrics['frqP10'][dom][mon], metrics['frqP20'][dom][mon], metrics['frqP80'][dom][mon], metrics['frqP90'][dom][mon], metrics['amtP10'][dom][mon], metrics['amtP20'][dom][mon], metrics['amtP80'][dom][mon], metrics['amtP90'][dom][mon] = CalcP10P90(pdfdom[im,:,idm], amtdom[im,:,idm], amtdom_ref[im,:,idm], bincrates)

            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[im,:,idm], bincrates)
                metrics['frqpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['frqwidth'][dom]['CalendarMonths'][imn] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[im,:,idm], bincrates)
                metrics['amtpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['amtwidth'][dom]['CalendarMonths'][imn] = rainwidth
                metrics['pscore'][dom]['CalendarMonths'][imn] = CalcPscore(pdfdom[im,:,idm], pdfdom_ref[im,:,idm])

                metrics['frqP10'][dom]['CalendarMonths'][imn], metrics['frqP20'][dom]['CalendarMonths'][imn], metrics['frqP80'][dom]['CalendarMonths'][imn], metrics['frqP90'][dom]['CalendarMonths'][imn], metrics['amtP10'][dom]['CalendarMonths'][imn], metrics['amtP20'][dom]['CalendarMonths'][imn], metrics['amtP80'][dom]['CalendarMonths'][imn], metrics['amtP90'][dom]['CalendarMonths'][imn] = CalcP10P90(pdfdom[im,:,idm], amtdom[im,:,idm], amtdom_ref[im,:,idm], bincrates)

    print("Completed clustering domain metrics")
    return metrics, pdfdom, amtdom


# ==================================================================================
def CalcMetricsDomainAR6(pdf, amt, months, bincrates, dat, ref, ref_dir):
    """
    Input
    - pdf: pdf
    - amt: amount distribution
    - months: month list of input data
    - bincrates: bin centers
    - dat: data name
    - ref: reference data name
    - ref_dir: reference data directory
    Output
    - metrics: metrics for each domain
    - pdfdom: pdf for each domain
    - amtdom: amt for each domain
    """
    ar6_all = regionmask.defined_regions.ar6.all
    ar6_land = regionmask.defined_regions.ar6.land
    ar6_ocean = regionmask.defined_regions.ar6.ocean

    land_names = ar6_land.names
    land_abbrevs = ar6_land.abbrevs

    ocean_names = [ 'Arctic-Ocean',
                    'Arabian-Sea', 'Bay-of-Bengal', 'Equatorial-Indian-Ocean', 'S.Indian-Ocean',
                    'N.Pacific-Ocean', 'N.W.Pacific-Ocean', 'N.E.Pacific-Ocean', 'Pacific-ITCZ',
                    'S.W.Pacific-Ocean', 'S.E.Pacific-Ocean', 'N.Atlantic-Ocean', 'N.E.Atlantic-Ocean',
                    'Atlantic-ITCZ', 'S.Atlantic-Ocean', 'Southern-Ocean',
                  ]
    ocean_abbrevs = [ 'ARO',
                      'ARS', 'BOB', 'EIO', 'SIO',
                      'NPO', 'NWPO', 'NEPO', 'PITCZ',
                      'SWPO', 'SEPO', 'NAO', 'NEAO',
                      'AITCZ', 'SAO', 'SOO',
                    ]

    names = land_names + ocean_names
    abbrevs = land_abbrevs + ocean_abbrevs

    regions={}
    for reg in abbrevs:
        if reg in land_abbrevs or reg == 'ARO' or reg == 'ARS' or reg == 'BOB' or reg == 'EIO' or reg == 'SIO':
            vertices = ar6_all[reg].polygon
        elif reg == 'NPO':
            r1=[[132,20], [132,25], [157,50], [180,59.9], [180,25]]
            r2=[[-180,25], [-180,65], [-168,65], [-168,52.5], [-143,58], [-130,50], [-125.3,40]]
            vertices = MultiPolygon([Polygon(r1), Polygon(r2)])
        elif reg == 'NWPO':
            vertices = Polygon([[139.5,0], [132,5], [132,20], [180,25], [180,0]])
        elif reg == 'NEPO':
            vertices = Polygon([[-180,15], [-180,25], [-125.3,40], [-122.5,33.8], [-104.5,16]])
        elif reg == 'PITCZ':
            vertices = Polygon([[-180,0], [-180,15], [-104.5,16], [-83.4,2.2], [-83.4,0]])
        elif reg == 'SWPO':
            r1 = Polygon([[155,-30], [155,-10], [139.5,0], [180,0], [180,-30]])
            r2 = Polygon([[-180,-30], [-180,0], [-135,-10], [-135,-30]])
            vertices = MultiPolygon([Polygon(r1), Polygon(r2)])
        elif reg == 'SEPO':
            vertices = Polygon([[-135,-30], [-135,-10], [-180,0], [-83.4,0], [-83.4,-10], [-74.6,-20], [-78,-41]])
        elif reg == 'NAO':
            vertices = Polygon([[-70,25], [-77,31], [-50,50], [-50,58], [-42,58], [-38,62], [-10,62], [-10,40]])
        elif reg == 'NEAO':
            vertices = Polygon([[-52.5,10], [-70,25], [-10,40], [-10,30], [-20,30], [-20,10]])
        elif reg == 'AITCZ':
            vertices = Polygon([[-50,0], [-50,7.6], [-52.5,10], [-20,10], [-20,7.6], [8,0]])
        elif reg == 'SAO':
            vertices = Polygon([[-39.5,-25], [-34,-20], [-34,0], [8,0], [8,-36]])
        elif reg == 'EIO':
            vertices = Polygon([[139.5,0], [132,5], [132,20], [180,25], [180,0]])
        elif reg == 'SOO':
            vertices = Polygon([[-180,-56], [-180,-70], [-80,-70], [-65,-62], [-56,-62], [-56,-75], [-25,-75], [5,-64], [180,-64], [180,-50], [155,-50], [110,-36], [8,-36], [-39.5,-25], [-56,-40], [-56,-56], [-79,-56], [-79,-47], [-78,-41], [-135,-30], [-180,-30]])
        regions[reg]=vertices

    rdata=[]
    for reg in abbrevs:
        rdata.append(regions[reg])
    ar6_all_mod_ocn = regionmask.Regions(rdata, names=names, abbrevs=abbrevs, name="AR6 reference regions with modified ocean regions")


    ddom = []
    for d in [pdf, amt]:

        d = xr.DataArray.from_cdms2(d)
        mask_3D = ar6_all_mod_ocn.mask_3D(d, lon_name='longitude', lat_name='latitude')
        weights = np.cos(np.deg2rad(d.latitude))
        am = d.weighted(mask_3D * weights).mean(dim=("latitude", "longitude"))
        am = xr.DataArray.to_cdms2(am)

        ddom.append(am)

    ddom = MV.reshape(ddom,(-1,pdf.shape[0],pdf.shape[1],len(abbrevs)))
    print(ddom.shape)

    pdfdom = ddom[0]
    amtdom = ddom[1]
    axdom = cdms.createAxis(range(len(abbrevs)), id='domains')
    pdfdom.setAxisList((pdf.getAxis(0),pdf.getAxis(1),axdom))
    amtdom.setAxisList((pdf.getAxis(0),pdf.getAxis(1),axdom))

    if dat == ref:
        pdfdom_ref = pdfdom
        amtdom_ref = amtdom
    else:
        file = 'dist_frq.amt_domainAR6_regrid.'+str(pdf.shape[3])+"x"+str(pdf.shape[2])+'_'+ref+'.nc'
        pdfdom_ref = cdms.open(os.path.join(ref_dir, file))['pdf']
        amtdom_ref = cdms.open(os.path.join(ref_dir, file))['amt']

    metrics={}
    metrics['frqpeak']={}
    metrics['frqwidth']={}
    metrics['amtpeak']={}
    metrics['amtwidth']={}
    metrics['pscore']={}
    metrics['frqP10']={}
    metrics['frqP20']={}
    metrics['frqP80']={}
    metrics['frqP90']={}
    metrics['amtP10']={}
    metrics['amtP20']={}
    metrics['amtP80']={}
    metrics['amtP90']={}
    for idm, dom in enumerate(abbrevs):
        metrics['frqpeak'][dom]={'CalendarMonths':{}}
        metrics['frqwidth'][dom]={'CalendarMonths':{}}
        metrics['amtpeak'][dom]={'CalendarMonths':{}}
        metrics['amtwidth'][dom]={'CalendarMonths':{}}
        metrics['pscore'][dom]={'CalendarMonths':{}}
        metrics['frqP10'][dom]={'CalendarMonths':{}}
        metrics['frqP20'][dom]={'CalendarMonths':{}}
        metrics['frqP80'][dom]={'CalendarMonths':{}}
        metrics['frqP90'][dom]={'CalendarMonths':{}}
        metrics['amtP10'][dom]={'CalendarMonths':{}}
        metrics['amtP20'][dom]={'CalendarMonths':{}}
        metrics['amtP80'][dom]={'CalendarMonths':{}}
        metrics['amtP90'][dom]={'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[im,:,idm], bincrates)
                metrics['frqpeak'][dom][mon] = rainpeak
                metrics['frqwidth'][dom][mon] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[im,:,idm], bincrates)
                metrics['amtpeak'][dom][mon] = rainpeak
                metrics['amtwidth'][dom][mon] = rainwidth
                metrics['pscore'][dom][mon] = CalcPscore(pdfdom[im,:,idm], pdfdom_ref[im,:,idm])

                metrics['frqP10'][dom][mon], metrics['frqP20'][dom][mon], metrics['frqP80'][dom][mon], metrics['frqP90'][dom][mon], metrics['amtP10'][dom][mon], metrics['amtP20'][dom][mon], metrics['amtP80'][dom][mon], metrics['amtP90'][dom][mon] = CalcP10P90(pdfdom[im,:,idm], amtdom[im,:,idm], amtdom_ref[im,:,idm], bincrates)

            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[im,:,idm], bincrates)
                metrics['frqpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['frqwidth'][dom]['CalendarMonths'][imn] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[im,:,idm], bincrates)
                metrics['amtpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['amtwidth'][dom]['CalendarMonths'][imn] = rainwidth
                metrics['pscore'][dom]['CalendarMonths'][imn] = CalcPscore(pdfdom[im,:,idm], pdfdom_ref[im,:,idm])

                metrics['frqP10'][dom]['CalendarMonths'][imn], metrics['frqP20'][dom]['CalendarMonths'][imn], metrics['frqP80'][dom]['CalendarMonths'][imn], metrics['frqP90'][dom]['CalendarMonths'][imn], metrics['amtP10'][dom]['CalendarMonths'][imn], metrics['amtP20'][dom]['CalendarMonths'][imn], metrics['amtP80'][dom]['CalendarMonths'][imn], metrics['amtP90'][dom]['CalendarMonths'][imn] = CalcP10P90(pdfdom[im,:,idm], amtdom[im,:,idm], amtdom_ref[im,:,idm], bincrates)

    print("Completed AR6 domain metrics")
    return metrics, pdfdom, amtdom


# ==================================================================================
def CalcPscore(pdf, pdf_ref):
    """
    Input
    - pdf: pdf
    - pdf_ref: pdf reference for Perkins score
    Output
    - pscore: Perkins score
    """
    pdf = pdf.filled(np.nan)
    pdf_ref = pdf_ref.filled(np.nan)

    pscore = np.sum(np.minimum(pdf, pdf_ref), axis=0)
    pscore = np.array(pscore).tolist()

    return pscore


# ==================================================================================
def CalcP10P90(pdf, amt, amt_ref, bincrates):
    """
    Input
    - pdf: pdf
    - amt: amount distribution
    - amt_ref: amt reference
    - bincrates: bin centers
    Output
    - f10: fraction of frequency for lower 10 percentile amount
    - f20: fraction of frequency for lower 20 percentile amount
    - f80: fraction of frequency for upper 80 percentile amount
    - f90: fraction of frequency for upper 90 percentile amount
    - a10: fraction of amount for lower 10 percentile amount
    - a20: fraction of amount for lower 20 percentile amount
    - a80: fraction of amount for upper 80 percentile amount
    - a90: fraction of amount for upper 90 percentile amount
    """
    pdf = pdf.filled(np.nan)
    amt = amt.filled(np.nan)
    amt_ref = amt_ref.filled(np.nan)

    # Days with precip<0.1mm/day are considered dry (Pendergrass and Deser 2017)
    thidx=np.argwhere(bincrates>0.1)
    thidx=int(thidx[0][0])
    pdf[:thidx] = 0
    amt[:thidx] = 0
    amt_ref[:thidx] = 0
    #-----------------------------------------------------

    # Cumulative PDF
    # csum_pdf=np.cumsum(pdf, axis=0)
    pdffrac=pdf/np.sum(pdf, axis=0)
    csum_pdf=np.cumsum(pdffrac, axis=0)

    # Cumulative amount fraction
    amtfrac=amt/np.sum(amt, axis=0)
    csum_amtfrac=np.cumsum(amtfrac, axis=0)

    # Reference cumulative amount fraction
    amtfrac_ref=amt_ref/np.sum(amt_ref, axis=0)
    csum_amtfrac_ref=np.cumsum(amtfrac_ref, axis=0)

    # Find 10, 20, 80, and 90 percentiles
    p10_all=np.argwhere(csum_amtfrac_ref<=0.1)
    p20_all=np.argwhere(csum_amtfrac_ref<=0.2)
    p80_all=np.argwhere(csum_amtfrac_ref>=0.8)
    p90_all=np.argwhere(csum_amtfrac_ref>=0.9)

    if np.array(p10_all).size==0:
        f10 = np.nan
        a10 = np.nan
    else:
        p10 = int(p10_all[-1][0])
        f10 = csum_pdf[p10]
        a10 = csum_amtfrac[p10]

    if np.array(p20_all).size==0:
        f20 = np.nan
        a20 = np.nan
    else:
        p20 = int(p20_all[-1][0])
        f20 = csum_pdf[p20]
        a20 = csum_amtfrac[p20]

    if np.array(p80_all).size==0:
        f80 = np.nan
        a80 = np.nan
    else:
        p80 = int(p80_all[0][0])
        f80 = 1-csum_pdf[p80]
        a80 = 1-csum_amtfrac[p80]

    if np.array(p90_all).size==0:
        f90 = np.nan
        a90 = np.nan
    else:
        p90 = int(p90_all[0][0])
        f90 = 1-csum_pdf[p90]
        a90 = 1-csum_amtfrac[p90]

    f10 = np.array(f10).tolist()
    f20 = np.array(f20).tolist()
    f80 = np.array(f80).tolist()
    f90 = np.array(f90).tolist()
    a10 = np.array(a10).tolist()
    a20 = np.array(a20).tolist()
    a80 = np.array(a80).tolist()
    a90 = np.array(a90).tolist()

    return f10, f20, f80, f90, a10, a20, a80, a90


# ==================================================================================
def oneyear(thisyear, missingthresh):
    # Given one year of precip data, calculate the number of days for half of precipitation
    # Ignore years with zero precip (by setting them to NaN).
    # thisyear is one year of data, (an np array) with the time variable in the leftmost dimension

    thisyear = thisyear.filled(np.nan)  # np.array(thisyear)
    dims = thisyear.shape
    nd = dims[0]
    missingfrac = (np.sum(np.isnan(thisyear), axis=0)/nd)
    ptot = np.sum(thisyear, axis=0)
    sortandflip = -np.sort(-thisyear, axis=0)
    cum_sum = np.cumsum(sortandflip, axis=0)
    ptotnp = np.array(ptot)
    ptotnp[np.where(ptotnp == 0)] = np.nan
    pfrac = cum_sum / np.tile(ptotnp[np.newaxis, :, :], [nd, 1, 1])
    ndhy = np.full((dims[1], dims[2]), np.nan)
    prdays = np.full((dims[1], dims[2]), np.nan)
    prdays_gt_1mm = np.full((dims[1], dims[2]), np.nan)
    x = np.linspace(0, nd, num=nd+1, endpoint=True)
    z = np.array([0.0])
    for ij in range(dims[1]):
        for ik in range(dims[2]):
            p = pfrac[:, ij, ik]
            y = np.concatenate([z, p])
            ndh = np.interp(0.5, y, x)
            ndhy[ij, ik] = ndh
            if np.isnan(ptotnp[ij, ik]):
                prdays[ij, ik] = np.nan
                prdays_gt_1mm[ij, ik] = np.nan
            else:
                # For the case, pfrac does not reach 1 (maybe due to regridding)
                # prdays[ij,ik] = np.where(y >= 1)[0][0]
                prdays[ij, ik] = np.nanargmax(y)
                if np.diff(cum_sum[:, ij, ik])[-1] >= 1:
                    prdays_gt_1mm[ij, ik] = prdays[ij, ik]
                else:
                    prdays_gt_1mm[ij, ik] = np.where(
                        np.diff(np.concatenate([z, cum_sum[:, ij, ik]])) < 1)[0][0]

    ndhy[np.where(missingfrac > missingthresh)] = np.nan
    # prdyfrac = prdays/nd
    prdyfrac = prdays_gt_1mm/nd
    # sdii = ptot/prdays
    sdii = ptot/prdays_gt_1mm # Zhang et al. (2011)

    return pfrac, ndhy, prdyfrac, sdii


# ==================================================================================
def MedDomain(d, months):
    """
    Domain average
    Input
    - d: cdms variable
    - months: month list of input data
    Output
    - ddom: Domain median data (json)
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
            am = genutil.statistics.median(dmask(latitude=(-50, 50)), axis="xy")
        if "30N50N" in dom:
            am = genutil.statistics.median(dmask(latitude=(30, 50)), axis="xy")
        if "30S30N" in dom:
            am = genutil.statistics.median(dmask(latitude=(-30, 30)), axis="xy")
        if "50S30S" in dom:
            am = genutil.statistics.median(dmask(latitude=(-50, -30)), axis="xy")

        ddom[dom] = {'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:
                ddom[dom][mon] = am.tolist()[0][im]
            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                ddom[dom]['CalendarMonths'][imn] = am.tolist()[0][im]

    print("Completed domain median")
    return ddom


# ==================================================================================
def MedDomain3Clust(d, months):
    """
    Domain average
    Input
    - d: cdms variable
    - months: month list of input data
    Output
    - ddom: Domain median data (json)
    """
    domains = ["Total_HR_50S50N", "Total_MR_50S50N", "Total_LR_50S50N",
               "Total_HR_30N50N", "Total_MR_30N50N", "Total_LR_30N50N",
               "Total_HR_30S30N", "Total_MR_30S30N", "Total_LR_30S30N",
               "Total_HR_50S30S", "Total_MR_50S30S", "Total_LR_50S30S",
               "Ocean_HR_50S50N", "Ocean_MR_50S50N", "Ocean_LR_50S50N",
               "Ocean_HR_30N50N", "Ocean_MR_30N50N", "Ocean_LR_30N50N",
               "Ocean_HR_30S30N", "Ocean_MR_30S30N", "Ocean_LR_30S30N",
               "Ocean_HR_50S30S", "Ocean_MR_50S30S", "Ocean_LR_50S30S",
               "Land_HR_50S50N", "Land_MR_50S50N", "Land_LR_50S50N",
               "Land_HR_30N50N", "Land_MR_30N50N", "Land_LR_30N50N",
               "Land_HR_30S30N", "Land_MR_30S30N", "Land_LR_30S30N",
               "Land_HR_50S30S", "Land_MR_50S30S", "Land_LR_50S30S"]

    indir = '../lib'
    file = 'cluster3_pdf.amt_regrid.360x180_IMERG_ALL.nc'
    cluster = xr.open_dataset(os.path.join(indir, file))['cluster_nb']

    regs=['HR', 'MR', 'LR']
    mpolygons=[]
    regs_name=[]
    for irg, reg in enumerate(regs):
        if reg=='HR':
            data=xr.where(cluster==0, 1, 0)
            regs_name.append('Heavy precipitating region')
        elif reg=='MR':
            data=xr.where(cluster==1, 1, 0)
            regs_name.append('Moderate precipitating region')
        elif reg=='LR':
            data=xr.where(cluster==2, 1, 0)
            regs_name.append('Light precipitating region')
        else:
            print('ERROR: data is not defined')
            exit()

        shapes = rasterio.features.shapes(np.int32(data))

        polygons=[]
        for ish, shape in enumerate(shapes):
            for idx, xy in enumerate(shape[0]["coordinates"][0]):
                lst = list(xy)
                lst[0] = lst[0]
                lst[1] = lst[1]-89.5
                tup = tuple(lst)
                shape[0]["coordinates"][0][idx]=tup
            if shape[1] == 1:
                polygons.append(Polygon(shape[0]["coordinates"][0]))

        mpolygons.append(MultiPolygon(polygons).simplify(3, preserve_topology=False))

    region = regionmask.Regions(mpolygons, names=regs_name, abbrevs=regs, name="Heavy/Moderate/Light precipitating regions")
    print(region)

    d_xr = xr.DataArray.from_cdms2(d)
    mask_3D = region.mask_3D(d_xr, lon_name='longitude', lat_name='latitude')
    mask_3D = xr.DataArray.to_cdms2(mask_3D)

    mask = cdutil.generateLandSeaMask(d)
    mask_3D, mask2 = genutil.grower(mask_3D, mask)
    mask_3D_ocn = MV.where(mask2 == 0.0, mask_3D, False)
    mask_3D_lnd = MV.where(mask2 == 1.0, mask_3D, False)

    ddom = {}
    for dom in domains:
        if "Ocean" in dom:
            mask_3D_tmp = mask_3D_ocn
        elif "Land" in dom:
            mask_3D_tmp = mask_3D_lnd
        else:
            mask_3D_tmp = mask_3D

        if "HR" in dom:
            d, mask3 = genutil.grower(d, mask_3D_tmp[0,:,:])
        elif "MR" in dom:
            d, mask3 = genutil.grower(d, mask_3D_tmp[1,:,:])
        elif "LR" in dom:
            d, mask3 = genutil.grower(d, mask_3D_tmp[2,:,:])
        else:
            print('ERROR: HR/MR/LR is not defined')
            exit()

        dmask = MV.masked_where(~mask3, d)

        if "50S50N" in dom:
            am = genutil.statistics.median(dmask(latitude=(-50, 50)), axis="xy")
        if "30N50N" in dom:
            am = genutil.statistics.median(dmask(latitude=(30, 50)), axis="xy")
        if "30S30N" in dom:
            am = genutil.statistics.median(dmask(latitude=(-30, 30)), axis="xy")
        if "50S30S" in dom:
            am = genutil.statistics.median(dmask(latitude=(-50, -30)), axis="xy")

        ddom[dom] = {'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:
                ddom[dom][mon] = am.tolist()[0][im]
            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                ddom[dom]['CalendarMonths'][imn] = am.tolist()[0][im]

    print("Completed clustering domain median")
    return ddom


# ==================================================================================
def MedDomainAR6(d, months):
    """
    Domain average
    Input
    - d: cdms variable
    - months: month list of input data
    Output
    - ddom: Domain median data (json)
    """
    ar6_all = regionmask.defined_regions.ar6.all
    ar6_land = regionmask.defined_regions.ar6.land
    ar6_ocean = regionmask.defined_regions.ar6.ocean

    land_names = ar6_land.names
    land_abbrevs = ar6_land.abbrevs

    ocean_names = [ 'Arctic-Ocean',
                    'Arabian-Sea', 'Bay-of-Bengal', 'Equatorial-Indian-Ocean', 'S.Indian-Ocean',
                    'N.Pacific-Ocean', 'N.W.Pacific-Ocean', 'N.E.Pacific-Ocean', 'Pacific-ITCZ',
                    'S.W.Pacific-Ocean', 'S.E.Pacific-Ocean', 'N.Atlantic-Ocean', 'N.E.Atlantic-Ocean',
                    'Atlantic-ITCZ', 'S.Atlantic-Ocean', 'Southern-Ocean',
                  ]
    ocean_abbrevs = [ 'ARO',
                      'ARS', 'BOB', 'EIO', 'SIO',
                      'NPO', 'NWPO', 'NEPO', 'PITCZ',
                      'SWPO', 'SEPO', 'NAO', 'NEAO',
                      'AITCZ', 'SAO', 'SOO',
                    ]

    names = land_names + ocean_names
    abbrevs = land_abbrevs + ocean_abbrevs

    regions={}
    for reg in abbrevs:
        if reg in land_abbrevs or reg == 'ARO' or reg == 'ARS' or reg == 'BOB' or reg == 'EIO' or reg == 'SIO':
            vertices = ar6_all[reg].polygon
        elif reg == 'NPO':
            r1=[[132,20], [132,25], [157,50], [180,59.9], [180,25]]
            r2=[[-180,25], [-180,65], [-168,65], [-168,52.5], [-143,58], [-130,50], [-125.3,40]]
            vertices = MultiPolygon([Polygon(r1), Polygon(r2)])
        elif reg == 'NWPO':
            vertices = Polygon([[139.5,0], [132,5], [132,20], [180,25], [180,0]])
        elif reg == 'NEPO':
            vertices = Polygon([[-180,15], [-180,25], [-125.3,40], [-122.5,33.8], [-104.5,16]])
        elif reg == 'PITCZ':
            vertices = Polygon([[-180,0], [-180,15], [-104.5,16], [-83.4,2.2], [-83.4,0]])
        elif reg == 'SWPO':
            r1 = Polygon([[155,-30], [155,-10], [139.5,0], [180,0], [180,-30]])
            r2 = Polygon([[-180,-30], [-180,0], [-135,-10], [-135,-30]])
            vertices = MultiPolygon([Polygon(r1), Polygon(r2)])
        elif reg == 'SEPO':
            vertices = Polygon([[-135,-30], [-135,-10], [-180,0], [-83.4,0], [-83.4,-10], [-74.6,-20], [-78,-41]])
        elif reg == 'NAO':
            vertices = Polygon([[-70,25], [-77,31], [-50,50], [-50,58], [-42,58], [-38,62], [-10,62], [-10,40]])
        elif reg == 'NEAO':
            vertices = Polygon([[-52.5,10], [-70,25], [-10,40], [-10,30], [-20,30], [-20,10]])
        elif reg == 'AITCZ':
            vertices = Polygon([[-50,0], [-50,7.6], [-52.5,10], [-20,10], [-20,7.6], [8,0]])
        elif reg == 'SAO':
            vertices = Polygon([[-39.5,-25], [-34,-20], [-34,0], [8,0], [8,-36]])
        elif reg == 'EIO':
            vertices = Polygon([[139.5,0], [132,5], [132,20], [180,25], [180,0]])
        elif reg == 'SOO':
            vertices = Polygon([[-180,-56], [-180,-70], [-80,-70], [-65,-62], [-56,-62], [-56,-75], [-25,-75], [5,-64], [180,-64], [180,-50], [155,-50], [110,-36], [8,-36], [-39.5,-25], [-56,-40], [-56,-56], [-79,-56], [-79,-47], [-78,-41], [-135,-30], [-180,-30]])
        regions[reg]=vertices

    rdata=[]
    for reg in abbrevs:
        rdata.append(regions[reg])
    ar6_all_mod_ocn = regionmask.Regions(rdata, names=names, abbrevs=abbrevs, name="AR6 reference regions with modified ocean regions")

    d = xr.DataArray.from_cdms2(d)
    mask_3D = ar6_all_mod_ocn.mask_3D(d, lon_name='longitude', lat_name='latitude')
    am = d.where(mask_3D).median(dim=("latitude", "longitude"))

    ddom = {}
    for idm, dom in enumerate(abbrevs):
        ddom[dom] = {'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:
                ddom[dom][mon] = am[im,idm].values.tolist()
            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                ddom[dom]['CalendarMonths'][imn] = am[im,idm].values.tolist()

    print("Completed AR6 domain median")
    return ddom

