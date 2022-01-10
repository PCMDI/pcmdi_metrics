import cdms2 as cdms
import MV2 as MV
import cdutil
import genutil
import numpy as np
import regionmask
import xarray as xr
from regrid2 import Horizontal
from shapely.geometry import Polygon, MultiPolygon
import sys


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
    nx = 360/res[0]
    ny = 180/res[1]
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

    print("Complete regridding from", d.shape, "to", drg.shape)
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

        # msahn For treat noiend=[]
        if bool(noiend.any()) is False:
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
def AvgDomain(d):
    """
    Domain average
    Input
    - d: cdms variable
    Output
    - ddom: Domain averaged data (json)
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


# ==================================================================================
def CalcMetricsDomain(pdf_tn, amt, months, bincrates):
    """
    Input
    - pdf_tn: pdf with total number
    - amt: amount distribution
    - months: month list of the input data
    - bincrates: bin centers
    Output
    - metrics: metrics for each domain
    - pdfdom: pdf for each domain
    - amtdom: amt for each domain
    """    
    domains = ["Total_50S50N", "Ocean_50S50N", "Land_50S50N",
               "Total_30N50N", "Ocean_30N50N", "Land_30N50N",
               "Total_30S30N", "Ocean_30S30N", "Land_30S30N",
               "Total_50S30S", "Ocean_50S30S", "Land_50S30S"]

    pdf_tn_sum = cdutil.averager(pdf_tn, axis=1, weights='unweighted', action='sum')
    pdf_tn_sum = MV.repeat(MV.reshape(pdf_tn_sum,(pdf_tn_sum.shape[0],-1,pdf_tn_sum.shape[1],pdf_tn_sum.shape[2])),repeats=pdf_tn.shape[1],axis=1)
    pdf_tn_sum.setAxisList(pdf_tn.getAxisList())
    
    amt_tn = amt*pdf_tn_sum
    amt_tn.setAxisList(pdf_tn.getAxisList())    
    
    domsum = []
    for d in [pdf_tn, amt_tn, pdf_tn_sum]:
    
        mask = cdutil.generateLandSeaMask(d[0,0])
        d, mask2 = genutil.grower(d, mask)
        d_ocean = MV.masked_where(mask2 == 1.0, d)
        d_land = MV.masked_where(mask2 == 0.0, d)

        ddom = []
        for dom in domains:

            if "Ocean" in dom:
                dmask = d_ocean
            elif "Land" in dom:
                dmask = d_land
            else:
                dmask = d

            if "50S50N" in dom:
                am = cdutil.averager(dmask(latitude=(-50, 50)), axis="xy", action='sum')
            if "30N50N" in dom:
                am = cdutil.averager(dmask(latitude=(30, 50)), axis="xy", action='sum')
            if "30S30N" in dom:
                am = cdutil.averager(dmask(latitude=(-30, 30)), axis="xy", action='sum')
            if "50S30S" in dom:
                am = cdutil.averager(dmask(latitude=(-50, -30)), axis="xy", action='sum')

            ddom.append(am)

        domsum.append(ddom)
     
    domsum = MV.reshape(domsum,(-1,len(domains),am.shape[0],am.shape[1]))
    print(domsum.shape)
    
    pdfdom = domsum[0]/domsum[2]
    amtdom = domsum[1]/domsum[2]
    axdom = cdms.createAxis(range(len(domains)), id='domains')
    pdfdom.setAxisList((axdom,am.getAxis(0),am.getAxis(1)))    
    amtdom.setAxisList((axdom,am.getAxis(0),am.getAxis(1)))    
    
    metrics={}
    metrics['pdfpeak']={}
    metrics['pdfwidth']={}
    metrics['amtpeak']={}
    metrics['amtwidth']={}
    for idm, dom in enumerate(domains):
        metrics['pdfpeak'][dom]={'CalendarMonths':{}}
        metrics['pdfwidth'][dom]={'CalendarMonths':{}}
        metrics['amtpeak'][dom]={'CalendarMonths':{}}
        metrics['amtwidth'][dom]={'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:            
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[idm,im,:], bincrates)
                metrics['pdfpeak'][dom][mon] = rainpeak
                metrics['pdfwidth'][dom][mon] = rainwidth        
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[idm,im,:], bincrates)
                metrics['amtpeak'][dom][mon] = rainpeak
                metrics['amtwidth'][dom][mon] = rainwidth 
            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[idm,im,:], bincrates)
                metrics['pdfpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['pdfwidth'][dom]['CalendarMonths'][imn] = rainwidth        
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[idm,im,:], bincrates)
                metrics['amtpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['amtwidth'][dom]['CalendarMonths'][imn] = rainwidth 
                
    print("Complete domain metrics")
    return metrics, pdfdom, amtdom


# ==================================================================================
def CalcMetricsDomain3Clust(pdf_tn, amt, months, bincrates, res):
    """
    Input
    - pdf_tn: pdf with total number
    - amt: amount distribution
    - months: month list of the input data
    - bincrates: bin centers
    Output
    - metrics: metrics for each domain
    - pdfdom: pdf for each domain
    - amtdom: amt for each domain
    """ 
    indir = '/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717'
    file = 'cluster3_pdf.amt_regrid.'+res+'_IMERG_ALL.nc'
    cluster = cdms.open(os.path.join(indir, file))['cluster_nb']

    domains = ["HR_50S50N", "MR_50S50N", "LR_50S50N",
               "HR_30N50N", "MR_30N50N", "LR_30N50N",
               "HR_30S30N", "MR_30S30N", "LR_30S30N",
               "HR_50S30S", "MR_50S30S", "LR_50S30S"]

    pdf_tn_sum = cdutil.averager(pdf_tn, axis=1, weights='unweighted', action='sum')
    pdf_tn_sum = MV.repeat(MV.reshape(pdf_tn_sum,(pdf_tn_sum.shape[0],-1,pdf_tn_sum.shape[1],pdf_tn_sum.shape[2])),repeats=pdf_tn.shape[1],axis=1)
    pdf_tn_sum.setAxisList(pdf_tn.getAxisList())
    
    amt_tn = amt*pdf_tn_sum
    amt_tn.setAxisList(pdf_tn.getAxisList())    
        
    domsum = []
    for d in [pdf_tn, amt_tn, pdf_tn_sum]:
    
        d, mask2 = genutil.grower(d, cluster)
        d_HR = MV.masked_where(mask2 != 0, d)
        d_MR = MV.masked_where(mask2 != 1, d)
        d_LR = MV.masked_where(mask2 != 2, d)

        ddom = []
        for dom in domains:

            if "HR" in dom:
                dmask = d_HR
            elif "MR" in dom:
                dmask = d_MR
            elif "LR" in dom:
                dmask = d_LR

            if "50S50N" in dom:
                am = cdutil.averager(dmask(latitude=(-50, 50)), axis="xy", action='sum')
            if "30N50N" in dom:
                am = cdutil.averager(dmask(latitude=(30, 50)), axis="xy", action='sum')
            if "30S30N" in dom:
                am = cdutil.averager(dmask(latitude=(-30, 30)), axis="xy", action='sum')
            if "50S30S" in dom:
                am = cdutil.averager(dmask(latitude=(-50, -30)), axis="xy", action='sum')

            ddom.append(am)

        domsum.append(ddom)
        
    domsum = MV.reshape(domsum,(-1,len(domains),am.shape[0],am.shape[1]))
    print(domsum.shape)
    
    pdfdom = domsum[0]/domsum[2]
    amtdom = domsum[1]/domsum[2]
    axdom = cdms.createAxis(range(len(domains)), id='domains')
    pdfdom.setAxisList((axdom,am.getAxis(0),am.getAxis(1)))    
    amtdom.setAxisList((axdom,am.getAxis(0),am.getAxis(1)))    
    
    metrics={}
    metrics['pdfpeak']={}
    metrics['pdfwidth']={}
    metrics['amtpeak']={}
    metrics['amtwidth']={}
    for idm, dom in enumerate(domains):
        metrics['pdfpeak'][dom]={'CalendarMonths':{}}
        metrics['pdfwidth'][dom]={'CalendarMonths':{}}
        metrics['amtpeak'][dom]={'CalendarMonths':{}}
        metrics['amtwidth'][dom]={'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:            
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[idm,im,:], bincrates)
                metrics['pdfpeak'][dom][mon] = rainpeak
                metrics['pdfwidth'][dom][mon] = rainwidth        
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[idm,im,:], bincrates)
                metrics['amtpeak'][dom][mon] = rainpeak
                metrics['amtwidth'][dom][mon] = rainwidth 
            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[idm,im,:], bincrates)
                metrics['pdfpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['pdfwidth'][dom]['CalendarMonths'][imn] = rainwidth        
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[idm,im,:], bincrates)
                metrics['amtpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['amtwidth'][dom]['CalendarMonths'][imn] = rainwidth 
                                     
    print("Complete clustering domain metrics")
    return metrics, pdfdom, amtdom            
            
            
# ==================================================================================
def CalcMetricsDomainAR6(pdf_tn, amt, months, bincrates):
    """
    Input
    - pdf_tn: pdf with total number
    - amt: amount distribution
    - months: month list of the input data
    - bincrates: bin centers
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


    pdf_tn_sum = cdutil.averager(pdf_tn, axis=1, weights='unweighted', action='sum')
    pdf_tn_sum = MV.repeat(MV.reshape(pdf_tn_sum,(pdf_tn_sum.shape[0],-1,pdf_tn_sum.shape[1],pdf_tn_sum.shape[2])),repeats=pdf_tn.shape[1],axis=1)
    pdf_tn_sum.setAxisList(pdf_tn.getAxisList())
    
    amt_tn = amt*pdf_tn_sum
    amt_tn.setAxisList(pdf_tn.getAxisList())    
    
    domsum = []
    for d in [pdf_tn, amt_tn, pdf_tn_sum]:
    
        d = xr.DataArray.from_cdms2(d)
        mask_3D = ar6_all_mod_ocn.mask_3D(d, lon_name='longitude', lat_name='latitude')
        weights = np.cos(np.deg2rad(d.latitude))
        ddom = d.weighted(mask_3D * weights).sum(dim=("latitude", "longitude"))
        ddom = xr.DataArray.to_cdms2(ddom)
        
        domsum.append(ddom)
        
    domsum = MV.reshape(domsum,(-1,pdf_tn.shape[0],pdf_tn.shape[1],len(abbrevs)))
    domsum = np.swapaxes(domsum,1,3)
    domsum = np.swapaxes(domsum,2,3)
    print(domsum.shape)
    
    pdfdom = domsum[0]/domsum[2]
    amtdom = domsum[1]/domsum[2]
    axdom = cdms.createAxis(range(len(abbrevs)), id='domains')
    pdfdom.setAxisList((axdom,pdf_tn.getAxis(0),pdf_tn.getAxis(1)))    
    amtdom.setAxisList((axdom,pdf_tn.getAxis(0),pdf_tn.getAxis(1)))    
    
    metrics={}
    metrics['pdfpeak']={}
    metrics['pdfwidth']={}
    metrics['amtpeak']={}
    metrics['amtwidth']={}
    for idm, dom in enumerate(abbrevs):
        metrics['pdfpeak'][dom]={'CalendarMonths':{}}
        metrics['pdfwidth'][dom]={'CalendarMonths':{}}
        metrics['amtpeak'][dom]={'CalendarMonths':{}}
        metrics['amtwidth'][dom]={'CalendarMonths':{}}
        for im, mon in enumerate(months):
            if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:            
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[idm,im,:], bincrates)
                metrics['pdfpeak'][dom][mon] = rainpeak
                metrics['pdfwidth'][dom][mon] = rainwidth        
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[idm,im,:], bincrates)
                metrics['amtpeak'][dom][mon] = rainpeak
                metrics['amtwidth'][dom][mon] = rainwidth 
            else:
                calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                imn=calmon.index(mon)+1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(pdfdom[idm,im,:], bincrates)
                metrics['pdfpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['pdfwidth'][dom]['CalendarMonths'][imn] = rainwidth        
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(amtdom[idm,im,:], bincrates)
                metrics['amtpeak'][dom]['CalendarMonths'][imn] = rainpeak
                metrics['amtwidth'][dom]['CalendarMonths'][imn] = rainwidth                     
                
    print("Complete AR6 domain metrics")
    return metrics, pdfdom, amtdom     

