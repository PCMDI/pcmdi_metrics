import cdms2 as cdms
import MV2 as MV
import cdutil
import genutil
import numpy as np
import regionmask
import rasterio.features
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

    print("Complete domain median")
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
    
    indir = '/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20220108/diagnostic_results/precip_distribution/obs/v20220108'
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

    print("Complete clustering domain median")
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
           
    print("Complete AR6 domain median")
    return ddom

