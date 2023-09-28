#!/usr/bin/env python
# coding: utf-8

# =============================================
# Performs the cloud feedback and cloud error
# metric calculations in preparation for comparing
# to expert-assessed values from Sherwood et al (2020)
# =============================================

# IMPORT STUFF:
import cftime
import xarray as xr
import xcdat as xc
import numpy as np
from global_land_mask import globe
from datetime import date

# =============================================
# define necessary information
# =============================================

datadir = "../data/"

# Define a python dictionary containing the sections of the histogram to consider
# These are the same as in Zelinka et al, GRL, 2016
sections = ["ALL", "HI680", "LO680"]
Psections = [slice(0, 7), slice(2, 7), slice(0, 2)]
sec_dic = dict(zip(sections, Psections))

# 10 hPa/dy wide bins:
width = 10
binedges = np.arange(-100, 100, width)
x1 = np.arange(binedges[0] - width, binedges[-1] + 2 * width, width)
binmids = x1 + width / 2.0
cutoff = int(len(binmids) / 2)
# [:cutoff] = ascent; [cutoff:-1] = descent; [-1] = land

# load land sea mask (90x144):
lat = np.arange(-89, 90, 2.0)
lon = np.arange(1.25, 360, 2.5) - 180
lon_grid, lat_grid = np.meshgrid(lon, lat)
land_mask = globe.is_land(lat_grid, lon_grid)
land_mask = xr.DataArray(
    data=land_mask,
    dims=["lat", "lon"],
    coords=dict(lon=lon, lat=lat),
)
E = land_mask.sel(lon=slice(0, 180)).copy()
W = land_mask.sel(lon=slice(-180, 0)).copy()
W["lon"] = W["lon"] + 360
land_mask = xr.concat((E, W), dim="lon")
land_mask = xr.where(land_mask, 1.0, 0.0)
ocean_mask = xr.where(land_mask == 1.0, 0.0, 1.0)
del E, W


###########################################################################
def get_amip_data(filename, var, lev=None):
    # load in cmip data using the appropriate function for the experiment/mip
    print('  '+var)#, end=",")

    tslice = slice(
        "1983-01-01", "2008-12-31"
    )  # we only want this portion of the amip run (overlap with all AMIPs and ISCCP)

    f = xc.open_mfdataset(
        filename[var], chunks={"lat": -1, "lon": -1, "time": -1}
    ).load()
    if lev:
        f = f.sel(time=tslice, plev=lev)
        f = f.drop_vars(["plev", "plev_bnds"])
    else:
        f = f.sel(time=tslice)

    # Compute climatological monthly means
    avg = f.temporal.climatology(var, freq="month", weighted=True)
    # Regrid to cloud kernel grid
    output_grid = xc.create_grid(land_mask.lat.values, land_mask.lon.values)
    output = avg.regridder.horizontal(
        var, output_grid, tool="xesmf", method="bilinear", extrap_method="inverse_dist"
    )

    return output


###########################################################################
def get_model_data(filepath):
    # Read in data, regrid

    # Load in regridded monthly mean climatologies from control and perturbed simulation
    variables = ["tas", "rsdscs", "rsuscs", "wap", "clisccp"]
    print("amip")
    exp = "amip"
    ctl = []
    for var in variables:
        if "wap" in var:
            ctl.append(get_amip_data(filepath[exp], var, 50000))
        else:
            ctl.append(get_amip_data(filepath[exp], var))
    ctl = xr.merge(ctl)

    print("amip-p4K")
    exp = "amip-p4K"
    fut = []
    for var in variables:
        if "wap" in var:
            fut.append(get_amip_data(filepath[exp], var, 50000))
        else:
            fut.append(get_amip_data(filepath[exp], var))
    fut = xr.merge(fut)

    # set tau,plev to consistent field
    ctl["clisccp"] = ctl["clisccp"].transpose("time", "tau", "plev", "lat", "lon")
    fut["clisccp"] = fut["clisccp"].transpose("time", "tau", "plev", "lat", "lon")
    ctl["tau"] = np.arange(7)
    ctl["plev"] = np.arange(7)
    fut["tau"] = np.arange(7)
    fut["plev"] = np.arange(7)

    # Make sure wap is in hPa/day
    ctl["wap"] = 36 * 24 * ctl["wap"]  # Pa s-1 --> hPa/day
    fut["wap"] = 36 * 24 * fut["wap"]  # Pa s-1 --> hPa/day

    # Make sure clisccp is in percent
    sumclisccp1 = ctl["clisccp"].sum(dim=["tau", "plev"])
    if np.max(sumclisccp1) <= 1.0:
        ctl["clisccp"] = ctl["clisccp"] * 100.0
        fut["clisccp"] = fut["clisccp"] * 100.0

    return (ctl, fut)


###########################################################################
def get_CRK_data(filepath):
    # Read in data, regrid

    # Load in regridded monthly mean climatologies from control and perturbed simulation
    print("get data")
    ctl, fut = get_model_data(filepath)
    print("get LW and SW kernel")
    LWK, SWK = get_kernel_regrid(ctl)

    # global mean and annual average delta tas
    avgdtas0 = fut["tas"] - ctl["tas"]
    avgdtas0 = xc_to_dataset(avgdtas0)
    avgdtas0 = avgdtas0.spatial.average("data", axis=["X", "Y"])["data"]
    dTs = avgdtas0.mean()

    print("Sort into omega500 bins")
    ctl_wap_ocean = (ctl["wap"] * ocean_mask).sel(lat=slice(-30, 30))
    ctl_wap_land = (ctl["wap"] * land_mask).sel(lat=slice(-30, 30))
    fut_wap_ocean = (fut["wap"] * ocean_mask).sel(lat=slice(-30, 30))
    fut_wap_land = (fut["wap"] * land_mask).sel(lat=slice(-30, 30))

    ctl_OKwaps = bony_sorting_part1(ctl_wap_ocean, binedges)
    fut_OKwaps = bony_sorting_part1(fut_wap_ocean, binedges)

    area_wts = get_area_wts(ctl["tas"])  # summing this over lat and lon = 1
    WTS = area_wts.sel(lat=slice(-30, 30))
    TCC = ctl.clisccp.sel(lat=slice(-30, 30))
    TFC = fut.clisccp.sel(lat=slice(-30, 30))
    TLK = LWK.sel(lat=slice(-30, 30))
    TSK = SWK.sel(lat=slice(-30, 30))

    ctl_clisccp_wap, ctl_N = bony_sorting_part2(
        ctl_OKwaps, TCC, ctl_wap_land, WTS, binedges
    )
    fut_clisccp_wap, fut_N = bony_sorting_part2(
        fut_OKwaps, TFC, fut_wap_land, WTS, binedges
    )
    LWK_wap, P_wapbin = bony_sorting_part2(ctl_OKwaps, TLK, ctl_wap_land, WTS, binedges)
    SWK_wap, P_wapbin = bony_sorting_part2(ctl_OKwaps, TSK, ctl_wap_land, WTS, binedges)

    return (
        ctl.clisccp,
        fut.clisccp,
        LWK,
        SWK,
        dTs,
        area_wts,
        ctl_clisccp_wap,
        fut_clisccp_wap,
        LWK_wap,
        SWK_wap,
        ctl_N,
        fut_N,
    )


###########################################################################
def get_kernel_regrid(ctl):
    # Read in data and map kernels to lat/lon

    
    f = xc.open_mfdataset(datadir + "cloud_kernels2.nc", decode_times=False)
    f = f.rename({"mo": "time", "tau_midpt": "tau", "p_midpt": "plev"})
    f["time"] = ctl["time"].copy()
    f["tau"] = np.arange(7)
    f["plev"] = np.arange(7)  # set tau,plev to consistent field
    LWkernel = f["LWkernel"].isel(albcs=0).squeeze()  # two kernels file are different
    SWkernel = f["SWkernel"]
    del f

    # Compute clear-sky surface albedo
    ctl_albcs = ctl.rsuscs / ctl.rsdscs  # (12, 90, 144)
    ctl_albcs = ctl_albcs.fillna(0.0)
    ctl_albcs = ctl_albcs.where(~np.isinf(ctl_albcs), 0.0)
    ctl_albcs = xr.where(
        ctl_albcs > 1.0, 1, ctl_albcs
    )  # where(condition, x, y) is x where condition is true, y otherwise
    ctl_albcs = xr.where(ctl_albcs < 0.0, 0, ctl_albcs)

    # LW kernel does not depend on albcs, just repeat the final dimension over longitudes:
    LWK = LWkernel.expand_dims(dim=dict(lon=land_mask.lon), axis=4)

    # Use control albcs to map SW kernel to appropriate longitudes
    SWK = map_SWkern_to_lon(SWkernel, LWK, ctl_albcs)

    return LWK, SWK


###########################################################################
def map_SWkern_to_lon(SWkernel, LWK, albcsmap):
    """revised from zelinka_analysis.py"""

    from scipy.interpolate import interp1d

    ## Map each location's clear-sky surface albedo to the correct albedo bin
    # Ksw is size 12,7,7,lats,3
    # albcsmap is size 12,lats,lons
    albcs = np.arange(0.0, 1.5, 0.5)
    SWkernel_map = LWK.copy(data=nanarray(LWK.shape))

    for T in range(len(LWK.time)):
        for LAT in range(len(LWK.lat)):
            alon = albcsmap[T, LAT, :].copy()  # a longitude array
            if sum(~np.isnan(alon)) >= 1:  # at least 1 unmasked value
                if len(SWkernel[T, :, :, LAT, :] > 0) == 0:
                    SWkernel_map[T, :, :, LAT, :] = 0
                else:
                    f = interp1d(albcs, SWkernel[T, :, :, LAT, :], axis=2)
                    SWkernel_map[T, :, :, LAT, :] = f(alon.values)
            else:
                continue

    return SWkernel_map


###########################################################################
def nanarray(vector):
    # this generates a masked array with the size given by vector
    # example: vector = (90,144,28)
    # similar to this=NaN*ones(x,y,z) in matlab
    # used in "map_SWkern_to_lon"
    this = np.nan * np.ones(vector)
    return this


###########################################################################
def get_area_wts(idata):
    wgt1 = np.cos(np.deg2rad(idata.lat)) * (idata * 0 + 1)
    wgt1 = wgt1 / wgt1.sum(dim=["lat", "lon"])
    wgt1 = wgt1.transpose("time", "lat", "lon")

    return wgt1


###########################################################################
def compute_fbk(ctl, fut, DT):
    DR = fut - ctl
    fbk = DR / DT
    baseline = ctl
    return fbk, baseline


###########################################################################
def bony_sorting_part1(w500, binedges):
    """revised from bony_analysis.py"""

    w500 = xr.where(w500 == 0, np.nan, w500)
    A, B, C = w500.shape
    dx = np.diff(binedges)[0]
    # Compute composite:
    # add 2 for the exceedances
    OKwaps = xr.DataArray(
        data=nanarray((A, B, C, 2 + len(binedges))),
        dims=["time", "lat", "lon", "dwap"],
        coords=dict(
            time=w500.time,
            lat=w500.lat,
            lon=w500.lon,
            dwap=np.arange(2 + len(binedges)),
        ),
    )
    xx = 0
    for x in binedges:
        xx += 1
        w500_bin = xr.where(w500 >= x, w500, np.nan)
        OKwaps[:, :, :, xx] = xr.where(w500_bin < x + dx, w500_bin, np.nan)

    # do the first wap bin:
    OKwaps[:, :, :, 0] = xr.where(w500 < binedges[0], w500, np.nan)
    # do the last wap bin:
    OKwaps[:, :, :, -1] = xr.where(w500 >= binedges[-1] + dx, w500, np.nan)

    return OKwaps  # [month,lat,lon,wapbin]


###########################################################################
def bony_sorting_part2(OKwaps, data, OKland, WTS, binedges):
    """revised from bony_analysis.py"""

    # OKwaps # xarray(12, 30, 144, 22)
    # data # xarray(12, 7, 7, 30, 144)
    # OKland # xarray(12, 30, 144)
    # WTS # xarray(12,30,144)
    # binedges # numpy(20)

    # zeros and ones
    binary_waps = xr.where(np.isnan(OKwaps), 0.0, 1.0)  # xarray(12, 30, 144, 22)
    binary_land = xr.where(OKland == 0, 0.0, 1.0)  # xarray(12, 30, 144)
    binary_data = xr.where(np.isnan(data), 0.0, 1.0)  # xarray(12,7,7,30,144)

    # this function maps data from [time,...?,lat,lon] to [time,...?,wapbin]
    sh = list(data.shape[:-2])
    sh.append(3 + len(binedges))
    # add 2 for the exceedances, 1 for land, sh = [12, 7, 7, 23]
    DATA = xr.DataArray(
        data=nanarray((sh)),
        dims=["time", "tau", "plev", "dwap"],
        coords=dict(time=data.time, tau=data.tau, plev=data.plev, dwap=np.arange(23)),
    )
    sh = list()
    sh = np.append(data.shape[0], 3 + len(binedges))  # sh = [12,23]
    CNTS = xr.DataArray(
        data=nanarray((sh)),
        dims=["time", "dwap"],
        coords=dict(time=data.time, dwap=np.arange(23)),
    )
    # xarray(12, 23)

    A1b = binary_waps * WTS
    # zero for wap outside range, frac area for wap inside range
    # xarray(12,30,144,22)
    CNTS[:, :-1] = A1b.sum(dim=["lat", "lon"])
    # for ocean region
    # fractional area of this bin includes regions where data is undefined
    # xarray(12,23)

    for xx in range(2 + len(binedges)):
        A2 = binary_data * A1b.isel(dwap=xx)  # xarray(12,7,7,30,144)
        # zero for wap outside range or undefined data,
        # frac area for wap inside range
        denom = (A2).sum(dim=["lat", "lon"])  # xarray(12,7,7)
        numer = (data * A2).sum(dim=["lat", "lon"])  # xarray(12,7,7)
        DATA[:, :, :, xx] = numer / denom
        # bin-avg data is computed where both data and wap are defined

    # now do the land-only average:
    A1b = binary_land * WTS  # xarray(12,30,144)
    # zero for ocean points, frac area for land points
    CNTS[:, -1] = (A1b).sum(dim=["lat", "lon"])  # xarray(12,23)
    # fractional area of this bin includes regions where data is undefined
    A2 = binary_data * A1b  # xarray(12,7,7,30,144)
    # zero for ocean points or undefined data, frac area for land points
    denom = (A2).sum(dim=["lat", "lon"])  # xarray(12,7,7)
    numer = (data * A2).sum(dim=["lat", "lon"])  # xarray(12,7,7)
    DATA[:, :, :, -1] = numer / denom
    # bin-avg data is computed where both data and wap are defined

    # Ensure that the area matrix has zeros rather than masked points
    CNTS = CNTS.where(~np.isnan(CNTS), 0.0)

    if np.allclose(0.5, np.sum(CNTS.values, 1)) == False:
        print(
            "sum of fractional counts over all wapbins does not equal 0.5 (tropical fraction)"
        )
        # moot

    # DATA contains area-weighted averages within each bin
    # CNTS contains fractional areas represented by each bin
    # so summing (DATA*CNTS) over all regimes should recover
    # the tropical contribution to the global mean
    v1 = (DATA * CNTS).sum("dwap")
    # v2a = 0.5*gavg(data)
    v2b = (data * WTS).sum(dim=["lat", "lon"]).transpose("time", "tau", "plev")

    # if np.allclose(v1.values,v2a.values)==False or np.allclose(v1.values,v2b.values)==False:
    if np.allclose(v1.values, v2b.values) == False:
        print("Cannot reconstruct tropical average via summing regimes")

    return DATA, CNTS  # [time,wapbin]


###########################################################################
def KT_decomposition_general(c1, c2, Klw, Ksw):
    """
    this function takes in a (month,TAU,CTP,lat,lon) matrix and performs the
    decomposition of Zelinka et al 2013 doi:10.1175/JCLI-D-12-00555.1
    """

    sum_c = c1.sum(dim=["tau", "plev"])  # Eq. B2
    dc = c2 - c1
    sum_dc = dc.sum(dim=["tau", "plev"])
    dc_prop = c1 * (sum_dc / sum_c)
    dc_star = dc - dc_prop  # Eq. B1
    C_ratio = c1 / sum_c

    # LW components
    Klw0 = (Klw * c1 / sum_c).sum(dim=["tau", "plev"])  # Eq. B4
    Klw_prime = Klw - Klw0  # Eq. B3
    Klw_p_prime = (Klw_prime * (C_ratio.sum(dim="plev"))).sum(dim="tau")  # Eq. B7
    Klw_t_prime = (Klw_prime * (C_ratio.sum(dim="tau"))).sum(dim="plev")  # Eq. B8
    Klw_resid_prime = Klw_prime - Klw_p_prime - Klw_t_prime  # Eq. B9
    dRlw_true = (Klw * dc).sum(dim=["tau", "plev"])  # LW total
    dRlw_prop = Klw0 * sum_dc  # LW amount component
    dRlw_dctp = (Klw_p_prime * (dc_star.sum(dim="tau"))).sum(
        dim="plev"
    )  # LW altitude component
    dRlw_dtau = (Klw_t_prime * (dc_star.sum(dim="plev"))).sum(
        dim="tau"
    )  # LW tauical depth component
    dRlw_resid = (Klw_resid_prime * dc_star).sum(dim=["tau", "plev"])  # LW residual
    # dRlw_sum = dRlw_prop + dRlw_dctp + dRlw_dtau + dRlw_resid           # sum of LW components -- should equal LW total

    # SW components
    Ksw0 = (Ksw * c1 / sum_c).sum(dim=["tau", "plev"])  # Eq. B4
    Ksw_prime = Ksw - Ksw0  # Eq. B3
    Ksw_p_prime = (Ksw_prime * (C_ratio.sum(dim="plev"))).sum(dim="tau")  # Eq. B7
    Ksw_t_prime = (Ksw_prime * (C_ratio.sum(dim="tau"))).sum(dim="plev")  # Eq. B8
    Ksw_resid_prime = Ksw_prime - Ksw_p_prime - Ksw_t_prime  # Eq. B9
    dRsw_true = (Ksw * dc).sum(dim=["tau", "plev"])  # SW total
    dRsw_prop = Ksw0 * sum_dc  # SW amount component
    dRsw_dctp = (Ksw_p_prime * (dc_star.sum(dim="tau"))).sum(
        dim="plev"
    )  # SW altitude component
    dRsw_dtau = (Ksw_t_prime * (dc_star.sum(dim="plev"))).sum(
        dim="tau"
    )  # SW tauical depth component
    dRsw_resid = (Ksw_resid_prime * dc_star).sum(dim=["tau", "plev"])  # SW residual
    # dRsw_sum = dRsw_prop + dRsw_dctp + dRsw_dtau + dRsw_resid

    # Set SW fields to zero where the sun is down
    dRsw_true = xr.where(Ksw0 == 0, 0, dRsw_true)
    dRsw_prop = xr.where(Ksw0 == 0, 0, dRsw_prop)
    dRsw_dctp = xr.where(Ksw0 == 0, 0, dRsw_dctp)
    dRsw_dtau = xr.where(Ksw0 == 0, 0, dRsw_dtau)
    dRsw_resid = xr.where(Ksw0 == 0, 0, dRsw_resid)

    if "dwap" in c1.dims:
        output = {}
        output["LWcld_tot"] = dRlw_true.transpose("time", "dwap")
        output["LWcld_amt"] = dRlw_prop.transpose("time", "dwap")
        output["LWcld_alt"] = dRlw_dctp.transpose("time", "dwap")
        output["LWcld_tau"] = dRlw_dtau.transpose("time", "dwap")
        output["LWcld_err"] = dRlw_resid.transpose("time", "dwap")
        output["SWcld_tot"] = dRsw_true.transpose("time", "dwap")
        output["SWcld_amt"] = dRsw_prop.transpose("time", "dwap")
        output["SWcld_alt"] = dRsw_dctp.transpose("time", "dwap")
        output["SWcld_tau"] = dRsw_dtau.transpose("time", "dwap")
        output["SWcld_err"] = dRsw_resid.transpose("time", "dwap")

    else:
        output = {}
        output["LWcld_tot"] = dRlw_true.transpose("time", "lat", "lon")
        output["LWcld_amt"] = dRlw_prop.transpose("time", "lat", "lon")
        output["LWcld_alt"] = dRlw_dctp.transpose("time", "lat", "lon")
        output["LWcld_tau"] = dRlw_dtau.transpose("time", "lat", "lon")
        output["LWcld_err"] = dRlw_resid.transpose("time", "lat", "lon")
        output["SWcld_tot"] = dRsw_true.transpose("time", "lat", "lon")
        output["SWcld_amt"] = dRsw_prop.transpose("time", "lat", "lon")
        output["SWcld_alt"] = dRsw_dctp.transpose("time", "lat", "lon")
        output["SWcld_tau"] = dRsw_dtau.transpose("time", "lat", "lon")
        output["SWcld_err"] = dRsw_resid.transpose("time", "lat", "lon")

    return output


###########################################################################
def do_obscuration_calcs(CTL, FUT, Klw, Ksw, DT):
    (L_R_bar, dobsc, dunobsc, dobsc_cov) = obscuration_terms3(CTL, FUT)

    # Get unobscured low-cloud feedbacks and those caused by change in obscuration
    ZEROS = np.zeros(L_R_bar.shape)
    dummy, L_R_bar_base = compute_fbk(L_R_bar, L_R_bar, DT)
    dobsc_fbk, dummy = compute_fbk(ZEROS, dobsc, DT)
    dunobsc_fbk, dummy = compute_fbk(ZEROS, dunobsc, DT)
    dobsc_cov_fbk, dummy = compute_fbk(ZEROS, dobsc_cov, DT)
    obsc_output = obscuration_feedback_terms_general(
        L_R_bar_base, dobsc_fbk, dunobsc_fbk, dobsc_cov_fbk, Klw, Ksw
    )

    return obsc_output


###########################################################################
def obscuration_feedback_terms_general(
    L_R_bar0, dobsc_fbk, dunobsc_fbk, dobsc_cov_fbk, Klw, Ksw
):
    """
    Estimate unobscured low cloud feedback,
    the low cloud feedback arising solely from changes in obscuration by upper-level clouds,
    and the covariance term

    This function takes in a (month,tau,CTP,lat,lon) matrix

    Klw and Ksw contain just the low bins

    the following terms are generated in obscuration_terms():
    dobsc = L_R_bar0 * F_prime
    dunobsc = L_R_prime * F_bar
    dobsc_cov = (L_R_prime * F_prime) - climo(L_R_prime * F_prime)
    """

    Klw_low = Klw
    Ksw_low = Ksw
    L_R_bar0 = 100 * L_R_bar0
    dobsc_fbk = 100 * dobsc_fbk
    dunobsc_fbk = 100 * dunobsc_fbk
    dobsc_cov_fbk = 100 * dobsc_cov_fbk

    LWdobsc_fbk = (Klw_low * dobsc_fbk).sum(dim=["tau", "plev"])
    LWdunobsc_fbk = (Klw_low * dunobsc_fbk).sum(dim=["tau", "plev"])
    LWdobsc_cov_fbk = (Klw_low * dobsc_cov_fbk).sum(dim=["tau", "plev"])

    SWdobsc_fbk = (Ksw_low * dobsc_fbk).sum(dim=["tau", "plev"])
    SWdunobsc_fbk = (Ksw_low * dunobsc_fbk).sum(dim=["tau", "plev"])
    SWdobsc_cov_fbk = (Ksw_low * dobsc_cov_fbk).sum(dim=["tau", "plev"])

    ###########################################################################
    # Further break down the true and apparent low cloud-induced radiation anomalies into components
    ###########################################################################
    # No need to break down dobsc_fbk, as that is purely an amount component.

    # Break down dunobsc_fbk:
    C_ctl = L_R_bar0
    dC = dunobsc_fbk
    C_fut = C_ctl + dC

    obsc_fbk_output = KT_decomposition_general(C_ctl, C_fut, Klw_low, Ksw_low)

    obsc_fbk_output["LWdobsc_fbk"] = LWdobsc_fbk
    obsc_fbk_output["LWdunobsc_fbk"] = LWdunobsc_fbk
    obsc_fbk_output["LWdobsc_cov_fbk"] = LWdobsc_cov_fbk
    obsc_fbk_output["SWdobsc_fbk"] = SWdobsc_fbk
    obsc_fbk_output["SWdunobsc_fbk"] = SWdunobsc_fbk
    obsc_fbk_output["SWdobsc_cov_fbk"] = SWdobsc_cov_fbk

    return obsc_fbk_output


###########################################################################
def obscuration_terms3(c1, c2):
    """
    USE THIS VERSION FOR DIFFERENCES OF 2 CLIMATOLOGIES (E.G. AMIP4K, 2xCO2 SLAB RUNS)

    Compute the components required for the obscuration-affected low cloud feedback
    These are the terms shown in Eq 4 of Scott et al (2020) DOI: 10.1175/JCLI-D-19-1028.1
    L_prime = dunobsc + dobsc + dobsc_cov, where
    dunobsc = L_R_prime * F_bar     (delta unobscured low clouds, i.e., true low cloud feedback)
    dobsc = L_R_bar * F_prime       (delta obscuration by upper level clouds)
    dobsc_cov = (L_R_prime * F_prime) - climo(L_R_prime * F_prime)  (covariance term)
    """
    # c is [mo,tau,ctp,lat,lon]
    # c is in percent

    # SPLICE c1 and c2:
    # MAKE SURE c1 and c2 are the same size!!!
    if c1.shape != c2.shape:
        raise RuntimeError("c1 and c2 are NOT the same size!!!")

    c12 = xr.concat([c1, c2], dim="time")
    c12["time"] = xr.cftime_range(start="1983-01", periods=len(c12.time), freq="MS")

    midpt = len(c1)

    U12 = (c12[:, :, 2:, :]).sum(
        dim=["tau", "plev"]
    ) / 100.0  # [time, lat, lon] or [time, dwap]

    L12 = c12[:, :, :2, :] / 100.0

    F12 = 1.0 - U12
    F12 = xr.where(F12 >= 0, F12, np.nan)

    F12b = F12.expand_dims(dim=dict(tau=c12.tau), axis=1)
    F12b = F12b.expand_dims(dim=dict(plev=c12.plev), axis=2)

    L_R12 = L12 / F12  # L12/F12b
    sum_L_R12 = (L_R12).sum(dim=["tau", "plev"])
    sum_L_R12c = sum_L_R12.expand_dims(dim=dict(tau=L12.tau), axis=1)
    sum_L_R12c = sum_L_R12c.expand_dims(dim=dict(plev=L12.plev), axis=2)
    this = sum_L_R12c.where(sum_L_R12c <= 1, np.nan)
    this = this.where(this >= 0, np.nan)
    L_R12 = L_R12.where(~np.isnan(this), np.nan)
    L_R12 = L_R12.where(sum_L_R12c <= 1, np.nan)

    L_R_prime, L_R_bar = monthly_anomalies(L_R12)
    F_prime, F_bar = monthly_anomalies(F12b)
    L_prime, L_bar = monthly_anomalies(L12)

    # Cannot have negative cloud fractions:
    L_R_bar = L_R_bar.where(L_R_bar >= 0, 0.0)
    F_bar = F_bar.where(F_bar >= 0, 0.0)

    rep_L_bar = tile_uneven(L_bar, L12)
    rep_L_R_bar = tile_uneven(L_R_bar, L_R12)
    rep_F_bar = tile_uneven(F_bar, F12b)

    # Cannot have negative cloud fractions:
    L_R_bar = L_R_bar.where(L_R_bar >= 0, 0.0)
    F_bar = F_bar.where(F_bar >= 0, 0.0)

    dobsc = rep_L_R_bar * F_prime
    dunobsc = L_R_prime * rep_F_bar
    prime_prime = L_R_prime * F_prime

    dobsc_cov, climo_prime_prime = monthly_anomalies(prime_prime)

    # Re-scale these anomalies by 2, since we have computed all anomalies w.r.t.
    # the ctl+pert average rather than w.r.t. the ctl average
    dobsc *= 2
    dunobsc *= 2
    dobsc_cov *= 2

    # change time dimension
    Time = c1.time.copy()
    rep_L_R_bar_new = rep_L_R_bar[midpt:]
    rep_L_R_bar_new["time"] = Time
    dobsc_new = dobsc[midpt:]
    dobsc_new["time"] = Time
    dunobsc_new = dunobsc[midpt:]
    dunobsc_new["time"] = Time
    dobsc_cov_new = dobsc_cov[midpt:]
    dobsc_cov_new["time"] = Time

    return (rep_L_R_bar_new, dobsc_new, dunobsc_new, dobsc_cov_new)


###########################################################################
def xc_to_dataset(idata):
    idata = idata.to_dataset(name="data")
    if "height" in idata.coords:
        idata = idata.drop("height")
    idata = idata.bounds.add_missing_bounds()
    return idata


###########################################################################
def monthly_anomalies(idata):
    """
    Compute departures from the climatological annual cycle
    usage:
    anom,avg = monthly_anomalies(data)
    """
    idata = xc_to_dataset(idata)
    idata["time"].encoding["calendar"] = "noleap"
    clim = idata.temporal.climatology("data", freq="month", weighted=True)
    anom = idata.temporal.departures("data", freq="month", weighted=True)

    return (anom["data"], clim["data"])


###########################################################################
def tile_uneven(data, data_to_match):
    """extend data to match size of data_to_match even if not a multiple of 12"""

    A12 = len(data_to_match) // 12
    ind = np.arange(
        12,
    )
    rep_ind = np.tile(ind, (A12 + 1))[
        : int(len(data_to_match))
    ]  # int() added for python3

    rep_data = (data).isel(time=rep_ind)
    rep_data["time"] = data_to_match.time.copy()

    return rep_data


###########################################################################
def select_regions(field, region):
    if region == "eq90":
        field_dom = field.sel(lat=slice(-90, 90))
    elif region == "eq60":
        field_dom = field.sel(lat=slice(-60, 60))
    elif region == "eq30":
        field_dom = field.sel(lat=slice(-30, 30))
    elif region == "30-60":
        field1 = field.sel(lat=slice(-60, -30))
        field2 = field.sel(lat=slice(30, 60))
        field_dom = xr.concat([field1, field2], dim="lat")
    elif region == "30-80":
        field1 = field.sel(lat=slice(-80, -30))
        field2 = field.sel(lat=slice(30, 80))
        field_dom = xr.concat([field1, field2], dim="lat")
    elif region == "40-70":
        field1 = field.sel(lat=slice(-70, -40))
        field2 = field.sel(lat=slice(40, 70))
        field_dom = xr.concat([field1, field2], dim="lat")
    elif region == "Arctic":
        field_dom = field.sel(lat=slice(70, 90))
    return field_dom


###########################################################################
def do_klein_calcs(
    ctl_clisccp,
    LWK,
    SWK,
    WTS,
    ctl_clisccp_wap,
    LWK_wap,
    SWK_wap,
    obs_clisccp_AC,
    obs_clisccp_AC_wap,
    obs_N_AC_wap,
):
    KEM_dict = {}  # dictionary to contain all computed Klein error metrics
    for sec in sections:
        KEM_dict[sec] = {}
        PP = sec_dic[sec]
        C1 = ctl_clisccp[:, :, PP, :]
        Klw = LWK[:, :, PP, :]
        Ksw = SWK[:, :, PP, :]

        obs_C1 = obs_clisccp_AC[:, :, PP, :]
        ocn_obs_C1 = obs_C1 * ocean_mask
        lnd_obs_C1 = obs_C1 * land_mask
        ocn_C1 = C1 * ocean_mask
        lnd_C1 = C1 * land_mask

        # set ocean or land to nan
        ocn_obs_C1 = ocn_obs_C1.where(ocn_obs_C1 != 0.0, np.nan)
        lnd_obs_C1 = lnd_obs_C1.where(lnd_obs_C1 != 0.0, np.nan)
        ocn_C1 = ocn_C1.where(ocn_C1 != 0.0, np.nan)
        lnd_C1 = lnd_C1.where(lnd_C1 != 0.0, np.nan)

        # assessed feedback regions + Klein region (eq60)
        for region in ["eq90", "eq60", "eq30", "30-60", "30-80", "40-70", "Arctic"]:
            KEM_dict[sec][region] = {}
            obs_C1_dom = select_regions(obs_C1, region)
            ocn_obs_C1_dom = select_regions(ocn_obs_C1, region)
            lnd_obs_C1_dom = select_regions(lnd_obs_C1, region)
            C1_dom = select_regions(C1, region)
            ocn_C1_dom = select_regions(ocn_C1, region)
            lnd_C1_dom = select_regions(lnd_C1, region)
            Klw_dom = select_regions(Klw, region)
            Ksw_dom = select_regions(Ksw, region)
            WTS_dom = select_regions(WTS, region)
            for sfc in ["all", "ocn", "lnd", "ocn_asc", "ocn_dsc"]:
                KEM_dict[sec][region][sfc] = {}
                if sfc == "all":
                    (E_TCA, E_ctpt, E_LW, E_SW, E_NET) = klein_metrics(
                        obs_C1_dom, C1_dom, Klw_dom, Ksw_dom, WTS_dom
                    )
                elif sfc == "ocn":
                    (E_TCA, E_ctpt, E_LW, E_SW, E_NET) = klein_metrics(
                        ocn_obs_C1_dom, ocn_C1_dom, Klw_dom, Ksw_dom, WTS_dom
                    )
                elif sfc == "lnd":
                    (E_TCA, E_ctpt, E_LW, E_SW, E_NET) = klein_metrics(
                        lnd_obs_C1_dom, lnd_C1_dom, Klw_dom, Ksw_dom, WTS_dom
                    )
                else:
                    continue
                KEM_dict[sec][region][sfc]["E_TCA"] = E_TCA
                KEM_dict[sec][region][sfc]["E_ctpt"] = E_ctpt
                KEM_dict[sec][region][sfc]["E_LW"] = E_LW
                KEM_dict[sec][region][sfc]["E_SW"] = E_SW
                KEM_dict[sec][region][sfc]["E_NET"] = E_NET

        C1 = ctl_clisccp_wap[:, :, PP, :-1]
        obs_C1 = obs_clisccp_AC_wap[:, :, PP, :-1]  # ignore the land bin
        WTS_wap = obs_N_AC_wap[:, :-1]  # ignore the land bin
        Klw_wap = LWK_wap[:, :, PP, :-1]  # ignore the land bin
        Ksw_wap = SWK_wap[:, :, PP, :-1]
        (E_TCA, E_ctpt, E_LW, E_SW, E_NET) = klein_metrics(
            obs_C1[..., :cutoff],
            C1[..., :cutoff],
            Klw_wap[..., :cutoff],
            Ksw_wap[..., :cutoff],
            WTS_wap[:, :cutoff],
        )
        KEM_dict[sec]["eq30"]["ocn_asc"]["E_TCA"] = E_TCA
        KEM_dict[sec]["eq30"]["ocn_asc"]["E_ctpt"] = E_ctpt
        KEM_dict[sec]["eq30"]["ocn_asc"]["E_LW"] = E_LW
        KEM_dict[sec]["eq30"]["ocn_asc"]["E_SW"] = E_SW
        KEM_dict[sec]["eq30"]["ocn_asc"]["E_NET"] = E_NET

        ### this part is changed ###
        (E_TCA, E_ctpt, E_LW, E_SW, E_NET) = klein_metrics(
            obs_C1[..., cutoff:],
            C1[..., cutoff:],
            Klw_wap[..., cutoff:],
            Ksw_wap[..., cutoff:],
            WTS_wap[:, cutoff:],
        )
        KEM_dict[sec]["eq30"]["ocn_dsc"]["E_TCA"] = E_TCA
        KEM_dict[sec]["eq30"]["ocn_dsc"]["E_ctpt"] = E_ctpt
        KEM_dict[sec]["eq30"]["ocn_dsc"]["E_LW"] = E_LW
        KEM_dict[sec]["eq30"]["ocn_dsc"]["E_SW"] = E_SW
        KEM_dict[sec]["eq30"]["ocn_dsc"]["E_NET"] = E_NET

    # end for sec in sections:
    KEM_dict["metadata"] = {}
    meta = {
        "date_modified": str(date.today()),
        "author": "Mark D. Zelinka <zelinka1@llnl.gov> and Li-Wei Chao <chao5@llnl.gov>",
    }
    KEM_dict["metadata"] = meta

    return KEM_dict


###########################################################################
def klein_metrics(obs_clisccp, gcm_clisccp, LWkern, SWkern, WTS):
    ########################################################
    ######### Compute Klein et al (2013) metrics ###########
    ########################################################

    # Remove the thinnest optical depth bin from models/kernels so as to compare properly with obs:
    gcm_clisccp = gcm_clisccp[:, 1:, :, :]  # 6 tau bins
    LWkern = LWkern[:, 1:, :, :]
    SWkern = SWkern[:, 1:, :, :]

    obs_clisccp["tau"] = np.arange(6)
    gcm_clisccp["tau"] = np.arange(6)  # tau start from 1 so need to redefine tau
    LWkern["tau"] = np.arange(6)
    SWkern["tau"] = np.arange(6)

    ## Compute Cloud Fraction Histogram Anomalies w.r.t. observations
    clisccp_bias = gcm_clisccp - obs_clisccp

    ## Multiply Anomalies by Kernels
    SW = SWkern * clisccp_bias
    LW = LWkern * clisccp_bias
    NET = SW + LW

    ########################################################
    # E_TCA (TOTAL CLOUD AMOUNT METRIC)
    ########################################################
    # take only clouds with tau>1.3
    WTS_domavg = WTS / 12
    WTS_domavg = WTS_domavg / np.sum(WTS_domavg)
    # np.sum(WTS_dom) = 1, so weighted sums give area-weighted avg, NOT scaled by fraction of planet
    obs_clisccp_TCA = obs_clisccp[:, 1:, :]  # 5 tau bins
    gcm_clisccp_TCA = gcm_clisccp[:, 1:, :]  # 5 tau bins

    # sum over CTP and TAU:
    gcm_cltisccp_TCA = gcm_clisccp_TCA.sum(dim=["tau", "plev"])  # (time, lat, lon)
    obs_cltisccp_TCA = obs_clisccp_TCA.sum(dim=["tau", "plev"])  # (time, lat, lon)

    gcm_cltisccp_TCA = gcm_cltisccp_TCA.where(
        gcm_cltisccp_TCA != 0.0, np.nan
    )  # sum of nan will give 0, so make it nan again
    obs_cltisccp_TCA = obs_cltisccp_TCA.where(obs_cltisccp_TCA != 0.0, np.nan)

    # 1) Denominator (Eq. 3 in Klein et al. (2013))
    avg = (obs_cltisccp_TCA * WTS_domavg).sum()  # (scalar)
    anom1 = obs_cltisccp_TCA - avg  # anomaly of obs from its spatio-temporal mean
    # 2) Numerator -- Model minus ISCCP
    anom2 = gcm_cltisccp_TCA - obs_cltisccp_TCA  # (time, lat, lon)

    E_TCA_denom = np.sqrt((WTS_domavg * (anom1**2)).sum())  # (scalar)
    E_TCA_numer2 = np.sqrt((WTS_domavg * (anom2**2)).sum())  # (scalar)

    E_TCA = E_TCA_numer2 / E_TCA_denom

    ########################################################
    # CLOUD PROPERTY METRICS
    ########################################################
    # take only clouds with tau>3.6
    clisccp_bias_CPM = clisccp_bias[:, 2:, :]  # 4 tau bins
    obs_clisccp_CPM = obs_clisccp[:, 2:, :]  # 4 tau bins
    gcm_clisccp_CPM = gcm_clisccp[:, 2:, :]  # 4 tau bins
    LWkernel_CPM = LWkern[:, 2:, :]  # 4 tau bins
    SWkernel_CPM = SWkern[:, 2:, :]  # 4 tau bins
    NETkernel_CPM = SWkernel_CPM + LWkernel_CPM

    # Compute anomaly of obs histogram from its spatio-temporal mean
    if "dwap" in WTS_domavg.dims:  # working in wap space
        avg_obs_clisccp_CPM = (obs_clisccp_CPM * WTS_domavg).sum(
            dim=["time", "dwap"]
        )  # (TAU,CTP)
    else:  # working in lat/lon space
        avg_obs_clisccp_CPM = (obs_clisccp_CPM * WTS_domavg).sum(
            dim=["time", "lat", "lon"]
        )  # (TAU,CTP)
    anom_obs_clisccp_CPM = obs_clisccp_CPM - avg_obs_clisccp_CPM

    ## Compute radiative impacts of cloud fraction anomalies
    gcm_NET_bias = NET[:, 2:, :]  # 4 tau bins
    obs_NET_bias = anom_obs_clisccp_CPM * NETkernel_CPM
    gcm_SW_bias = SW[:, 2:, :]
    obs_SW_bias = anom_obs_clisccp_CPM * SWkernel_CPM
    gcm_LW_bias = LW[:, 2:, :]
    obs_LW_bias = anom_obs_clisccp_CPM * LWkernel_CPM

    ## Aggregate high, mid, and low clouds over medium and thick ISCCP ranges
    # Psec_name = ['LO','MID','HI']
    # Tsec_name = ['MED','THICK']
    if len(obs_clisccp.plev) == 7:
        Psec = [slice(0, 2), slice(2, 4), slice(4, 7)]
    elif len(obs_clisccp.plev) == 2:
        Psec = [slice(0, 2)]
    elif len(obs_clisccp.plev) == 5:
        Psec = [slice(0, 2), slice(2, 5)]

    Tsec = [slice(0, 2), slice(2, 4)]

    NP = len(Psec)
    NT = len(Tsec)

    agg_obs_NET_bias = gcm_NET_bias[:, :NT, :NP, :].copy() * 0.0
    agg_gcm_NET_bias = gcm_NET_bias[:, :NT, :NP, :].copy() * 0.0
    agg_obs_SW_bias = gcm_NET_bias[:, :NT, :NP, :].copy() * 0.0
    agg_gcm_SW_bias = gcm_NET_bias[:, :NT, :NP, :].copy() * 0.0
    agg_obs_LW_bias = gcm_NET_bias[:, :NT, :NP, :].copy() * 0.0
    agg_gcm_LW_bias = gcm_NET_bias[:, :NT, :NP, :].copy() * 0.0
    agg_obs_clisccp_bias = gcm_NET_bias[:, :NT, :NP, :].copy() * 0.0
    agg_gcm_clisccp_bias = gcm_NET_bias[:, :NT, :NP, :].copy() * 0.0

    obs_NET_bias = obs_NET_bias.where(~np.isnan(obs_NET_bias), 0)  # set nan to zero
    gcm_NET_bias = gcm_NET_bias.where(~np.isnan(gcm_NET_bias), 0)
    obs_SW_bias = obs_SW_bias.where(~np.isnan(obs_SW_bias), 0)
    gcm_SW_bias = gcm_SW_bias.where(~np.isnan(gcm_SW_bias), 0)
    obs_LW_bias = obs_LW_bias.where(~np.isnan(obs_LW_bias), 0)
    gcm_LW_bias = gcm_LW_bias.where(~np.isnan(gcm_LW_bias), 0)
    anom_obs_clisccp_CPM = anom_obs_clisccp_CPM.where(
        ~np.isnan(anom_obs_clisccp_CPM), 0
    )
    clisccp_bias_CPM = clisccp_bias_CPM.where(~np.isnan(clisccp_bias_CPM), 0)

    for tt, TT in enumerate(Tsec):
        for pp, PP in enumerate(Psec):
            agg_obs_NET_bias[:, tt, pp, :] = obs_NET_bias[:, TT, PP, :].sum(
                dim=["tau", "plev"]
            )
            agg_gcm_NET_bias[:, tt, pp, :] = gcm_NET_bias[:, TT, PP, :].sum(
                dim=["tau", "plev"]
            )
            agg_obs_SW_bias[:, tt, pp, :] = obs_SW_bias[:, TT, PP, :].sum(
                dim=["tau", "plev"]
            )
            agg_gcm_SW_bias[:, tt, pp, :] = gcm_SW_bias[:, TT, PP, :].sum(
                dim=["tau", "plev"]
            )
            agg_obs_LW_bias[:, tt, pp, :] = obs_LW_bias[:, TT, PP, :].sum(
                dim=["tau", "plev"]
            )
            agg_gcm_LW_bias[:, tt, pp, :] = gcm_LW_bias[:, TT, PP, :].sum(
                dim=["tau", "plev"]
            )
            agg_obs_clisccp_bias[:, tt, pp, :] = anom_obs_clisccp_CPM[:, TT, PP, :].sum(
                dim=["tau", "plev"]
            )
            agg_gcm_clisccp_bias[:, tt, pp, :] = clisccp_bias_CPM[:, TT, PP, :].sum(
                dim=["tau", "plev"]
            )

    ## Compute E_ctp-tau -- Cloud properties error
    ctot1 = (agg_gcm_clisccp_bias**2).sum(dim=["tau", "plev"]) / (NT * NP)
    ctot2 = (agg_obs_clisccp_bias**2).sum(dim=["tau", "plev"]) / (NT * NP)

    ## Compute E_LW -- LW-relevant cloud properties error
    ctot3 = (agg_gcm_LW_bias**2).sum(dim=["tau", "plev"]) / (NT * NP)
    ctot4 = (agg_obs_LW_bias**2).sum(dim=["tau", "plev"]) / (NT * NP)

    ## Compute E_SW -- SW-relevant cloud properties error
    ctot5 = (agg_gcm_SW_bias**2).sum(dim=["tau", "plev"]) / (NT * NP)
    ctot6 = (agg_obs_SW_bias**2).sum(dim=["tau", "plev"]) / (NT * NP)

    ## Compute E_NET -- NET-relevant cloud properties error
    ctot7 = (agg_gcm_NET_bias**2).sum(dim=["tau", "plev"]) / (NT * NP)
    ctot8 = (agg_obs_NET_bias**2).sum(dim=["tau", "plev"]) / (NT * NP)

    # compute one metric
    E_ctpt_numer = np.sqrt((WTS_domavg * ctot1).sum())  # (scalar)
    E_ctpt_denom = np.sqrt((WTS_domavg * ctot2).sum())  # (scalar)
    E_LW_numer = np.sqrt((WTS_domavg * ctot3).sum())  # (scalar)
    E_LW_denom = np.sqrt((WTS_domavg * ctot4).sum())  # (scalar)
    E_SW_numer = np.sqrt((WTS_domavg * ctot5).sum())  # (scalar)
    E_SW_denom = np.sqrt((WTS_domavg * ctot6).sum())  # (scalar)
    E_NET_numer = np.sqrt((WTS_domavg * ctot7).sum())  # (scalar)
    E_NET_denom = np.sqrt((WTS_domavg * ctot8).sum())  # (scalar)

    E_ctpt = E_ctpt_numer / E_ctpt_denom
    E_LW = E_LW_numer / E_LW_denom
    E_SW = E_SW_numer / E_SW_denom
    E_NET = E_NET_numer / E_NET_denom

    return (E_TCA.values, E_ctpt.values, E_LW.values, E_SW.values, E_NET.values)


###########################################################################
def cal_Klein_metrics(
    ctl_clisccp, LWK, SWK, area_wts, ctl_clisccp_wap, LWK_wap, SWK_wap
):
    ##########################################################
    ##### Load in ISCCP HGG clisccp climo annual cycle  ######
    ##########################################################

    f = xc.open_dataset(datadir + "AC_clisccp_ISCCP_HGG_198301-200812.nc")
    # f.history='Written by /work/zelinka1/scripts/load_ISCCP_HGG.py on feedback.llnl.gov'
    # f.comment='Monthly-resolved climatological annual cycle over 198301-200812'
    obs_clisccp_AC = f["AC_clisccp"]
    obs_clisccp_AC = obs_clisccp_AC.rename({"tau_midpt": "tau", "p_midpt": "plev"})
    obs_clisccp_AC["time"] = ctl_clisccp["time"].copy(deep=True)
    obs_clisccp_AC["tau"] = np.arange(6)
    obs_clisccp_AC["plev"] = np.arange(7)
    del f

    f = xc.open_dataset(datadir + "AC_clisccp_wap_ISCCP_HGG_198301-200812.nc")
    # f.history='Written by /work/zelinka1/scripts/load_ISCCP_HGG.py on feedback.llnl.gov'
    # f.comment='Monthly-resolved climatological annual cycle over 198301-200812, in omega500 space'
    obs_clisccp_AC_wap = f["AC_clisccp_wap"]
    obs_clisccp_AC_wap = obs_clisccp_AC_wap.rename(
        {"tau_midpt": "tau", "p_midpt": "plev", "wap500_bin": "dwap"}
    )
    obs_clisccp_AC_wap["time"] = ctl_clisccp["time"].copy(deep=True)
    obs_clisccp_AC_wap["tau"] = np.arange(6)
    obs_clisccp_AC_wap["plev"] = np.arange(7)
    obs_clisccp_AC_wap["dwap"] = np.arange(23)

    obs_N_AC_wap = f["AC_N_wap"]
    obs_N_AC_wap = obs_N_AC_wap.rename({"wap500_bin": "dwap"})
    obs_N_AC_wap["time"] = ctl_clisccp["time"].copy(deep=True)
    obs_N_AC_wap["dwap"] = np.arange(23)
    del f

    KEM_dict = do_klein_calcs(
        ctl_clisccp,
        LWK,
        SWK,
        area_wts,
        ctl_clisccp_wap,
        LWK_wap,
        SWK_wap,
        obs_clisccp_AC,
        obs_clisccp_AC_wap,
        obs_N_AC_wap,
    )

    return KEM_dict


###########################################################################
def regional_breakdown(data, OCN, LND, area_wts, norm=False):
    # Compute spatial averages over various geographical regions, for ocean, land, and both
    # if norm=False (the default), these averages are scaled by the fractional area of the planet over which they occur
    # if norm=True, these are simply area-weighted averages

    ocn_area_wts = area_wts * OCN
    lnd_area_wts = area_wts * LND
    mx = np.arange(
        10, 101, 10
    )  # max latitude of region (i.e., from -mx to mx); last one is for Arctic
    denom = 1
    reg_dict = {}
    sections = list(data.keys())
    surfaces = ["all", "ocn", "lnd"]
    for r in mx:
        if r == 100:
            region = "Arctic"
            domain = slice(70, 90)
        else:
            region = "eq" + str(r)
            domain = slice(-r, r)
        reg_dict[region] = {}
        for sfc in surfaces:
            reg_dict[region][sfc] = {}
            for sec in sections:
                reg_dict[region][sfc][sec] = {}
                DATA = data[sec]
                names = list(DATA.keys())
                for name in names:
                    # reg_dict[region][sfc][sec][name] = {}
                    fbk = DATA[name]
                    fbk_wts = fbk * area_wts
                    if sfc == "ocn":
                        wtd_fbk = (
                            (fbk_wts * OCN).sel(lat=domain).sum(dim=["lat", "lon"])
                        )
                        if norm:
                            denom = (
                                (ocn_area_wts).sel(lat=domain).sum(dim=["lat", "lon"])
                            )
                    elif sfc == "lnd":
                        wtd_fbk = (
                            (fbk_wts * LND).sel(lat=domain).sum(dim=["lat", "lon"])
                        )
                        if norm:
                            denom = (
                                (lnd_area_wts).sel(lat=domain).sum(dim=["lat", "lon"])
                            )
                    elif sfc == "all":
                        wtd_fbk = (fbk_wts).sel(lat=domain).sum(dim=["lat", "lon"])
                        if norm:
                            denom = (area_wts).sel(lat=domain).sum(dim=["lat", "lon"])
                    wtd_fbk = wtd_fbk / denom
                    reg_dict[region][sfc][sec][name] = (wtd_fbk).mean("time").values

    # reserve spots in the dictionary for asc/dsc feedbacks
    reg_dict["eq30"]["ocn_asc"] = {}
    reg_dict["eq30"]["ocn_dsc"] = {}
    for sec in sections:
        reg_dict["eq30"]["ocn_asc"][sec] = {}
        reg_dict["eq30"]["ocn_dsc"][sec] = {}

    return reg_dict


###########################################################################
def CloudRadKernel(filepath):
    (
        ctl_clisccp,
        fut_clisccp,
        LWK,
        SWK,
        dTs,
        area_wts,
        ctl_clisccp_wap,
        fut_clisccp_wap,
        LWK_wap,
        SWK_wap,
        ctl_N,
        fut_N,
    ) = get_CRK_data(filepath)

    OCN = ocean_mask.copy()
    LND = land_mask.copy()

    ##############################################################################
    # Compute Klein et al cloud error metrics and their breakdown into components
    ##############################################################################
    print("Compute Klein et al error metrics")
    KEM_dict = cal_Klein_metrics(
        ctl_clisccp, LWK, SWK, area_wts, ctl_clisccp_wap, LWK_wap, SWK_wap
    )
    # [sec][region][sfc][ID], ID=E_TCA,E_ctpt,E_LW,E_SW,E_NET

    ###########################################################################
    # Compute cloud feedbacks and their breakdown into components
    ###########################################################################
    print("Compute feedbacks")
    clisccp_fbk, clisccp_base = compute_fbk(ctl_clisccp, fut_clisccp, dTs)
    # The following performs the amount/altitude/optical depth decomposition of
    # Zelinka et al., J Climate (2012b), as modified in Zelinka et al., J. Climate (2013)
    output = {}
    output_wap = {}
    for sec in sections:
        print("    for section " + sec)
        # [sec][flavor][region][all / ocn / lnd / ocn_asc / ocn_dsc]

        PP = sec_dic[sec]

        C1 = clisccp_base[:, :, PP, :]
        C2 = C1 + clisccp_fbk[:, :, PP, :]
        Klw = LWK[:, :, PP, :]
        Ksw = SWK[:, :, PP, :]

        output[sec] = KT_decomposition_general(C1, C2, Klw, Ksw)

        Klw = LWK_wap[:, :, PP, :-1]  # ignore the land bin
        Ksw = SWK_wap[:, :, PP, :-1]
        C1 = ctl_clisccp_wap[:, :, PP, :-1]
        C2 = fut_clisccp_wap[:, :, PP, :-1]
        N1 = ctl_N[:, :-1]
        N2 = fut_N[:, :-1]

        # no breakdown (this is identical to within + between + covariance)
        C1N1 = (C1 * N1).transpose(
            "time", "tau", "plev", "dwap"
        )  # [month,TAU,CTP,regime]
        C2N2 = (C2 * N2).transpose(
            "time", "tau", "plev", "dwap"
        )  # [month,TAU,CTP,regime]
        pert, C_base = compute_fbk(C1N1, C2N2, dTs)
        output_wap[sec] = KT_decomposition_general(C_base, C_base + pert, Klw, Ksw)

    ###########################################################################
    # Compute obscuration feedback components
    ###########################################################################
    print("Get Obscuration Terms")
    sec = "LO680"  # this should already be true, but just in case...
    PP = sec_dic[sec]
    obsc_output = {}
    obsc_output[sec] = do_obscuration_calcs(
        ctl_clisccp, fut_clisccp, LWK[:, :, PP, :], SWK[:, :, PP, :], dTs
    )

    # Do this for the omega-regimes too:
    CTL = (ctl_clisccp_wap * ctl_N)[..., :-1]  # ignore the land bin
    FUT = (fut_clisccp_wap * fut_N)[..., :-1]
    LWK_wap_tmp = LWK_wap[:, :, PP, :-1]  # ignore the land bin
    SWK_wap_tmp = SWK_wap[:, :, PP, :-1]  # ignore the land bin
    obsc_output_wap = {}
    obsc_output_wap[sec] = do_obscuration_calcs(CTL, FUT, LWK_wap_tmp, SWK_wap_tmp, dTs)

    ###########################################################################
    # Compute regional averages (weighted by fraction of globe); place in dictionary
    ###########################################################################
    print("Compute regional averages")
    # [region][sfc][sec][name]
    obsc_fbk_dict = regional_breakdown(obsc_output, OCN, LND, area_wts)
    fbk_dict = regional_breakdown(output, OCN, LND, area_wts)

    # Put all the ascending and descending region quantities in a dictionary
    names = list(output_wap["ALL"].keys())
    for sec in sections:
        for name in names:
            fbk_dict["eq30"]["ocn_asc"][sec][name] = (
                (output_wap[sec][name][:, :cutoff]).sum("dwap").mean("time").values
            )
            fbk_dict["eq30"]["ocn_dsc"][sec][name] = (
                (output_wap[sec][name][:, cutoff:]).sum("dwap").mean("time").values
            )

    sec = "LO680"
    names = list(obsc_output_wap[sec].keys())
    for name in names:
        obsc_fbk_dict["eq30"]["ocn_asc"][sec][name] = (
            (obsc_output_wap[sec][name][:, :cutoff]).sum("dwap").mean("time").values
        )
        obsc_fbk_dict["eq30"]["ocn_dsc"][sec][name] = (
            (obsc_output_wap[sec][name][:, cutoff:]).sum("dwap").mean("time").values
        )

    meta = {
        "date_modified": str(date.today()),
        "author": "Mark D. Zelinka <zelinka1@llnl.gov> and Li-Wei Chao <chao5@llnl.gov>",
    }
    fbk_dict["metadata"] = meta
    obsc_fbk_dict["metadata"] = meta

    return (fbk_dict, obsc_fbk_dict, KEM_dict)
