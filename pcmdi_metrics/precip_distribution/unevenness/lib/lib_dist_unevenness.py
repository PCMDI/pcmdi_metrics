import cdms2 as cdms
import MV2 as MV
import cdutil
import genutil
import numpy as np
from regrid2 import Horizontal
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
    - mon: month (e.g., 'JAN', 'FEB', 'MAR', ...)
    Output
    - calmo: cdms variable concatenated for specific month
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
            calmo = MV.concatenate((calmo, tmp), axis=0)
    return calmo


# ==================================================================================
def oneyear(thisyear, missingthresh):
    # Given one year of precip data, calculate the number of days for half of precipitation
    # Ignore years with zero precip (by setting them to NaN).
    # thisyear is one year of data, (an np array) with the time variable in the leftmost dimension
    dims=thisyear.shape
    nd=dims[0]
    missingfrac = (np.sum(np.isnan(thisyear),axis=0)/nd)
    ptot=np.sum(thisyear,axis=0)
    sortandflip=-np.sort(-thisyear,axis=0)
    cum_sum=np.cumsum(sortandflip,axis=0)
    ptotnp=np.array(ptot)
    ptotnp[np.where(ptotnp == 0)]=np.nan
    pfrac = cum_sum / np.tile(ptotnp[np.newaxis,:,:],[nd,1,1])
    ndhy = np.full((dims[1],dims[2]),np.nan)
    prdays = np.full((dims[1],dims[2]),np.nan)
    x=np.linspace(0,nd,num=nd+1,endpoint=True)
    z=np.array([0.0])
    for ij in range(dims[1]):
        for ik in range(dims[2]):
            p=pfrac[:,ij,ik]
            y=np.concatenate([z,p])
            ndh=np.interp(0.5,y,x)
            ndhy[ij,ik]=ndh
            if missingfrac[ij,ik] > missingthresh or np.sum(np.isnan(p))/nd > missingthresh:
                prdays[ij,ik] = np.nan
            else:
                prdays[ij,ik] = np.where(p >= 1)[0][0]+1
                
    ndhy[np.where(missingfrac > missingthresh)] = np.nan
    prdyfrac = prdays/nd
    sdii = ptot/prdays

    return pfrac, ndhy, prdyfrac, sdii


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
