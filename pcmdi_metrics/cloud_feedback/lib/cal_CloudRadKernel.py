#!/usr/bin/env python
# coding: utf-8

#=============================================
# Performs the cloud feedback and cloud error 
# metric calculations in preparation for comparing 
# to expert-assessed values from Sherwood et al (2020)
#=============================================

#IMPORT STUFF:
#=====================
import cdms2 as cdms
import cdutil
import MV2 as MV
import numpy as np
from datetime import date 
from genutil import grower
import bony_analysis as BA
import zelinka_analysis as ZA

datadir='../data/'

# Define a python dictionary containing the sections of the histogram to consider
# These are the same as in Zelinka et al, GRL, 2016
sections = ['ALL','HI680','LO680']
Psections=[slice(0,7),slice(2,7),slice(0,2)]
sec_dic=dict(zip(sections,Psections))

TR = cdutil.region.domain(latitude=(-30.,30.))
        
# 10 hPa/dy wide bins:
width = 10
binedges=np.arange(-100,100,width)
x1=np.arange(binedges[0]-width,binedges[-1]+2*width,width)
binmids = x1+width/2.
cutoff = np.int(len(binmids)/2) # [:cutoff] = ascent; [cutoff:-1] = descent; [-1] = land
      
# Load in the Zelinka et al 2012 kernels:
f=cdms.open(datadir+'cloud_kernels2.nc')
LWkernel=f('LWkernel')
SWkernel=f('SWkernel')
f.close()
LWkernel=MV.masked_where(np.isnan(LWkernel),LWkernel)
SWkernel=MV.masked_where(np.isnan(SWkernel),SWkernel)
albcs=np.arange(0.0,1.5,0.5) # the clear-sky albedos over which the kernel is computed

# Define the cloud kernel axis attributes
lats=cdms.createAxis(LWkernel.getLatitude()[:])
lats.id="lat" 
lats.units="degrees_N"
lats.designateLatitude()
lons=cdms.createAxis(np.arange(1.25,360,2.5))
lons.id="lon" 
lons.units="degrees_E"
lons.designateLongitude()
kern_grid = cdms.createGenericGrid(lats,lons)
kern_grid.getLatitude().id='lat'
kern_grid.getLongitude().id='lon'  


##########################################################
##### Load in ISCCP HGG clisccp climo annual cycle  ######
##########################################################
f=cdms.open(datadir+'AC_clisccp_ISCCP_HGG_198301-200812.nc','r')
#f.history='Written by /work/zelinka1/scripts/load_ISCCP_HGG.py on feedback.llnl.gov'
#f.comment='Monthly-resolved climatological annual cycle over 198301-200812'
obs_clisccp_AC = f('AC_clisccp')
f.close()  


f=cdms.open(datadir+'AC_clisccp_wap_ISCCP_HGG_198301-200812.nc','r')
#f.history='Written by /work/zelinka1/scripts/load_ISCCP_HGG.py on feedback.llnl.gov'
#f.comment='Monthly-resolved climatological annual cycle over 198301-200812, in omega500 space'
obs_clisccp_AC_wap = f('AC_clisccp_wap')
obs_N_AC_wap = f('AC_N_wap')
f.close()  

###########################################################################
def apply_land_mask_v2(data):
    """
    apply land mask (data):
    this will read in and reshape the land-sea mask to match data
    """
    # Call the cdutil function to generate a mask, 0 for ocean, 1 for land.
    mask = cdutil.generateLandSeaMask(data)

    # Match dimension using "grower" function
    data, mask2 = grower(data, mask)

    ocean_data = MV.masked_where(mask2, data)
    land_data = MV.masked_where(mask2==0., data)

    return (ocean_data,land_data)
    
###########################################################################
def apply_land_mask_v3(data,ocn_mask,lnd_mask):
    """
    apply land mask (data):
    this will read in and reshape the land-sea mask to match data
    """

    ocean_data = MV.masked_where(ocn_mask.mask, data)
    land_data = MV.masked_where(lnd_mask.mask, data)

    return (ocean_data,land_data)    
    
###############################################################################################
def compute_fbk(ctl,fut,DT):
    DR = fut - ctl
    fbk = DR/DT
    baseline = ctl
    return fbk,baseline


###############################################################################################
def do_klein_calcs(ctl_clisccp,LWK,SWK,obs_clisccp_AC,ctl_clisccp_wap,LWK_wap,SWK_wap,obs_clisccp_AC_wap,obs_N_AC_wap):
    KEM_dict = {} # dictionary to contain all computed Klein error metrics   
    for sec in sections:
        KEM_dict[sec]={}
        PP=sec_dic[sec]   
        C1 = ctl_clisccp[:,:,PP,:]
        Klw = LWK[:,:,PP,:]
        Ksw = SWK[:,:,PP,:]

        obs_C1 = obs_clisccp_AC[:,:,PP,:]
        ocn_obs_C1,lnd_obs_C1 = apply_land_mask_v2(obs_C1)
        ocn_C1,lnd_C1 = apply_land_mask_v2(C1)   
        
        WTS = get_area_wts(obs_C1[:,0,0,:]) # summing this over lat and lon = 1           
        for region in ['eq90','eq60','eq30','30-60','30-80','40-70','Arctic']: # assessed feedback regions + Klein region (eq60)
            KEM_dict[sec][region]={}
            obs_C1_dom = select_regions(obs_C1,region)
            ocn_obs_C1_dom = select_regions(ocn_obs_C1,region)
            lnd_obs_C1_dom = select_regions(lnd_obs_C1,region)
            C1_dom = select_regions(C1,region)
            ocn_C1_dom = select_regions(ocn_C1,region)
            lnd_C1_dom = select_regions(lnd_C1,region)
            Klw_dom = select_regions(Klw,region)
            Ksw_dom = select_regions(Ksw,region)
            WTS_dom = select_regions(WTS,region)                    
            for sfc in ['all','ocn','lnd','ocn_asc','ocn_dsc']:
                KEM_dict[sec][region][sfc]={}
                if sfc=='all':
                    (E_TCA,E_ctpt,E_LW,E_SW,E_NET) = klein_metrics(obs_C1_dom,C1_dom,Klw_dom,Ksw_dom,WTS_dom)
                elif sfc=='ocn':
                    (E_TCA,E_ctpt,E_LW,E_SW,E_NET) = klein_metrics(ocn_obs_C1_dom,ocn_C1_dom,Klw_dom,Ksw_dom,WTS_dom)
                elif sfc=='lnd':
                    (E_TCA,E_ctpt,E_LW,E_SW,E_NET) = klein_metrics(lnd_obs_C1_dom,lnd_C1_dom,Klw_dom,Ksw_dom,WTS_dom)
                else:
                    continue
                KEM_dict[sec][region][sfc]['E_TCA'] = E_TCA
                KEM_dict[sec][region][sfc]['E_ctpt'] = E_ctpt
                KEM_dict[sec][region][sfc]['E_LW'] = E_LW
                KEM_dict[sec][region][sfc]['E_SW'] = E_SW 
                KEM_dict[sec][region][sfc]['E_NET'] = E_NET     
                     
        C1 = ctl_clisccp_wap[:,:,PP,:-1]
        obs_C1 = obs_clisccp_AC_wap[:,:,PP,:-1] # ignore the land bin
        WTS = obs_N_AC_wap[:,:-1] # ignore the land bin
        Klw = LWK_wap[:,:,PP,:-1] # ignore the land bin
        Ksw = SWK_wap[:,:,PP,:-1]
        (E_TCA,E_ctpt,E_LW,E_SW,E_NET) = klein_metrics(obs_C1[...,:cutoff],C1[...,:cutoff],Klw[...,:cutoff],Ksw[...,:cutoff],WTS[:,:cutoff])
        KEM_dict[sec]['eq30']['ocn_asc']['E_TCA'] = E_TCA
        KEM_dict[sec]['eq30']['ocn_asc']['E_ctpt'] = E_ctpt
        KEM_dict[sec]['eq30']['ocn_asc']['E_LW'] = E_LW
        KEM_dict[sec]['eq30']['ocn_asc']['E_SW'] = E_SW  
        KEM_dict[sec]['eq30']['ocn_asc']['E_NET'] = E_NET
        (E_TCA,E_ctpt,E_LW,E_SW,E_NET) = klein_metrics(obs_C1[...,cutoff:-1],C1[...,cutoff:-1],Klw[...,cutoff:-1],Ksw[...,cutoff:-1],WTS[:,cutoff:-1])
        KEM_dict[sec]['eq30']['ocn_dsc']['E_TCA'] = E_TCA
        KEM_dict[sec]['eq30']['ocn_dsc']['E_ctpt'] = E_ctpt
        KEM_dict[sec]['eq30']['ocn_dsc']['E_LW'] = E_LW
        KEM_dict[sec]['eq30']['ocn_dsc']['E_SW'] = E_SW  
        KEM_dict[sec]['eq30']['ocn_dsc']['E_NET'] = E_NET 
    # end for sec in sections:
    KEM_dict['metadata'] = {}
    meta = {
    "date_modified" :   str(date.today()),
    "author"        :   "Mark D. Zelinka <zelinka1@llnl.gov>",
    }
    KEM_dict['metadata'] = meta

    return(KEM_dict)    
    
###########################################################################        
def do_obscuration_calcs(CTL,FUT,Klw,Ksw,DT):

    (L_R_bar,dobsc,dunobsc,dobsc_cov) = obscuration_terms3(CTL,FUT)

    # Get unobscured low-cloud feedbacks and those caused by change in obscuration        
    ZEROS = np.zeros(L_R_bar.shape)        
    dummy,L_R_bar_base = compute_fbk(L_R_bar,L_R_bar,DT) 
    dobsc_fbk,dummy = compute_fbk(ZEROS,dobsc,DT)
    dunobsc_fbk,dummy = compute_fbk(ZEROS,dunobsc,DT)
    dobsc_cov_fbk,dummy = compute_fbk(ZEROS,dobsc_cov,DT)
    obsc_output = obscuration_feedback_terms_general(L_R_bar_base,dobsc_fbk,dunobsc_fbk,dobsc_cov_fbk,Klw,Ksw)
    
    return(obsc_output)
        
###########################################################################        
def get_amip_data(filename,var,lev=None):
    # load in cmip data using the appropriate function for the experiment/mip

    print('        '+var)

    tslice = ("1983-01-01","2008-12-31") # we only want this portion of the amip run (overlap with all AMIPs and ISCCP)
    f=cdms.open(filename[var])
    if lev:
        data = f(var,time=tslice,level=lev,squeeze=1) 
    else:
        data = f(var,time=tslice,squeeze=1) 
    f.close()
    # Compute climatological monthly means       
    dummy,avg = monthly_anomalies(data)
    avg.setAxisList(data[:12,:].getAxisList())
    # Regrid to cloud kernel grid
    data = avg.regrid(kern_grid,regridTool="esmf",regridMethod = "linear")

    return(data)

###########################################################################
def get_area_wts(data):
    # Create map of area weights
    lats = data.getLatitude()
    lons = data.getLongitude()
    A,B,C = data.shape
    coslat = np.cos(lats[:]*np.pi/180)
    coslat2 = coslat/np.sum(coslat)
    area_wts = MV.array(np.moveaxis(np.tile(coslat2/C,[A,C,1]),1,2)) # summing this over lat and lon = 1
    area_wts.setAxis(1,lats)
    area_wts.setAxis(2,lons)
    return area_wts


###########################################################################
def get_CRK_data(filenames):
    # Read in data, regrid and map kernels to lat/lon
    
    # Load in regridded monthly mean climatologies from control and perturbed simulation
    print('    amip')
    ctl_tas = get_amip_data(filenames['amip'],'tas')
    ctl_rsdscs = get_amip_data(filenames['amip'],'rsdscs')
    ctl_rsuscs = get_amip_data(filenames['amip'],'rsuscs')
    ctl_wap = get_amip_data(filenames['amip'],'wap',50000)
    ctl_clisccp = get_amip_data(filenames['amip'],'clisccp')
    
    print('    amip-p4K')
    fut_tas = get_amip_data(filenames['amip-p4K'],'tas')
    fut_rsdscs = get_amip_data(filenames['amip-p4K'],'rsdscs')
    fut_rsuscs = get_amip_data(filenames['amip-p4K'],'rsuscs')
    fut_wap = get_amip_data(filenames['amip-p4K'],'wap',50000)
    fut_clisccp = get_amip_data(filenames['amip-p4K'],'clisccp')

    # Make sure wap is in hPa/day
    fut_wap = 36*24*fut_wap # Pa s-1 --> hPa/day 
    ctl_wap = 36*24*ctl_wap # Pa s-1 --> hPa/day    

    # Make sure clisccp is in percent  
    sumclisccp1=np.ma.sum(np.ma.sum(ctl_clisccp,2),1)
    if np.max(sumclisccp1) <= 1.:
        ctl_clisccp = ctl_clisccp*100.        
        fut_clisccp = fut_clisccp*100.  
        
    # Give clisccp axes info
    AXL = ctl_tas.getAxisList()
    ctl_clisccp.setAxis(0,AXL[0])
    ctl_clisccp.setAxis(3,AXL[1])
    ctl_clisccp.setAxis(4,AXL[2])
    fut_clisccp.setAxisList(ctl_clisccp.getAxisList())

    # Compute clear-sky surface albedo  
    ctl_albcs=ctl_rsuscs/ctl_rsdscs #(12, 90, 144)
    ctl_albcs=MV.where(ctl_albcs>1.,1,ctl_albcs) # where(condition, x, y) is x where condition is true, y otherwise
    ctl_albcs=MV.where(ctl_albcs<0.,0,ctl_albcs)    

    # The first month may not be January:
    yrs,mos = get_plottable_time(ctl_albcs)
    choose = mos - 1 # mos runs from 1-12, so subtract 1 to make an index         
                   
    # Use control albcs to map SW kernel to appropriate longitudes
    SWkernel_map = ZA.map_SWkern_to_lon(SWkernel,ctl_albcs)
    # LW kernel does not depend on albcs, just repeat the final dimension over longitudes:
    LWkernel_map=np.tile(np.tile(LWkernel[:,:,:,:,0],(1,1,1,1,1)),(144,1,1,1,1))(order=[1,2,3,4,0])
    LWkernel_map = MV.take(LWkernel_map, choose, axis=0)
    LWkernel_map.setAxisList(ctl_clisccp.getAxisList())
    SWkernel_map.setAxisList(ctl_clisccp.getAxisList())
    
    # global mean delta tas
    anom_tas = fut_tas - ctl_tas
    avgdtas0 = cdutil.averager(anom_tas, axis='xy', weights='weighted') # global average
    avgdtas0.setAxis(0,ctl_tas.getAxis(0))

    # compute annual averages
    avgdtas = YEAR(avgdtas0)

    print('Sort into omega500 bins')
    ctl_wap_ocean,ctl_wap_land = apply_land_mask_v2(TR.select(ctl_wap))
    fut_wap_ocean,fut_wap_land = apply_land_mask_v2(TR.select(fut_wap))
    ctl_OKwaps = BA.bony_sorting_part1(ctl_wap_ocean,binedges)
    fut_OKwaps = BA.bony_sorting_part1(fut_wap_ocean,binedges)
    
    area_wts = get_area_wts(ctl_tas) # summing this over lat and lon = 1
    WTS = TR.select(area_wts)
    TCC = TR.select(ctl_clisccp)
    TFC = TR.select(fut_clisccp)
    TLK = TR.select(LWkernel_map)
    TSK = TR.select(SWkernel_map)
    
    ctl_clisccp_wap, ctl_N = BA.bony_sorting_part2(ctl_OKwaps,TCC,ctl_wap_land,WTS,binedges)
    fut_clisccp_wap, fut_N = BA.bony_sorting_part2(fut_OKwaps,TFC,fut_wap_land,WTS,binedges)
    LWK_wap, P_wapbin = BA.bony_sorting_part2(ctl_OKwaps,TLK,ctl_wap_land,WTS,binedges)
    SWK_wap, P_wapbin = BA.bony_sorting_part2(ctl_OKwaps,TSK,ctl_wap_land,WTS,binedges)

    return(ctl_clisccp,fut_clisccp,LWkernel_map,SWkernel_map,avgdtas,ctl_clisccp_wap,fut_clisccp_wap,LWK_wap,SWK_wap,ctl_N,fut_N)


###########################################################################
def get_plottable_time(X):
    # Function stolen / modified from Kate Marvel
    years = [x.year+(x.month-1)/12. for x in X.getTime().asComponentTime()]
    months = [x.month for x in X.getTime().asComponentTime()]
    return (np.array(years),np.array(months))


###########################################################################
def klein_metrics(obs_clisccp,gcm_clisccp,LWkern,SWkern,WTS):

    ########################################################
    ######### Compute Klein et al (2013) metrics ########### 
    ########################################################
    
    # Remove the thinnest optical depth bin from models/kernels so as to compare properly with obs:
    gcm_clisccp = gcm_clisccp[:,1:,:,:]
    LWkern = LWkern[:,1:,:,:]
    SWkern = SWkern[:,1:,:,:]
    
    ## Compute Cloud Fraction Histogram Anomalies w.r.t. observations
    clisccp_bias = gcm_clisccp - obs_clisccp

    ## Multiply Anomalies by Kernels
    SW = SWkern*clisccp_bias
    LW = LWkern*clisccp_bias
    NET = SW+LW

    ########################################################
    # E_TCA (TOTAL CLOUD AMOUNT METRIC)
    ########################################################    
    # take only clouds with tau>1.3 
    WTS_dom = WTS/12 
    WTS_dom = WTS_dom/np.sum(WTS_dom) # np.sum(WTS_dom) = 1, so weighted sums give area-weighted avg, NOT scaled by fraction of planet 
    obs_clisccp_dom = obs_clisccp[:,1:,:]
    gcm_clisccp_dom = gcm_clisccp[:,1:,:]

    # sum over CTP and TAU:
    gcm_cltisccp_dom = MV.sum(MV.sum(gcm_clisccp_dom,1),1) # (time, lat, lon)
    obs_cltisccp_dom = MV.sum(MV.sum(obs_clisccp_dom,1),1) # (time, lat, lon)

    # 1) Denominator (Eq. 3 in Klein et al. (2013))
    avg = np.sum(obs_cltisccp_dom*WTS_dom) # (scalar)
    anom1 = obs_cltisccp_dom - avg # anomaly of obs from its spatio-temporal mean
    # 2) Numerator -- Model minus ISCCP
    anom2 = gcm_cltisccp_dom - obs_cltisccp_dom  # (time, lat, lon)

    E_TCA_denom = np.ma.sqrt(np.ma.sum(WTS_dom*anom1**2)) # (scalar)
    E_TCA_numer2 = np.ma.sqrt(np.ma.sum(WTS_dom*anom2**2)) # (scalar) 

    E_TCA = E_TCA_numer2/E_TCA_denom

    ########################################################
    # CLOUD PROPERTY METRICS
    ########################################################
    # take only clouds with tau>3.6 
    clisccp_bias_dom = clisccp_bias[:,2:,:]
    obs_clisccp_dom = obs_clisccp[:,2:,:]
    gcm_clisccp_dom = gcm_clisccp[:,2:,:]  
    LWkernel_dom = LWkern[:,2:,:]
    SWkernel_dom = SWkern[:,2:,:]  
    NETkernel_dom = SWkernel_dom + LWkernel_dom

    # Compute anomaly of obs histogram from its spatio-temporal mean
    this = np.moveaxis(obs_clisccp_dom,0,2) # [TAU,CTP,month,space]
    if np.ndim(WTS_dom)==2: # working in wap space
        avg_obs_clisccp_dom = np.ma.sum(np.ma.sum(this*WTS_dom,-1),-1) # (TAU,CTP)
    else: # working in lat/lon space
        avg_obs_clisccp_dom = np.ma.sum(np.ma.sum(np.ma.sum(this*WTS_dom,-1),-1),-1) # (TAU,CTP)
    this = np.moveaxis(np.moveaxis(obs_clisccp_dom,1,-1),1,-1) - avg_obs_clisccp_dom 
    anom_obs_clisccp_dom = np.moveaxis(np.moveaxis(this,-1,1),-1,1)

    ## Compute radiative impacts of cloud fraction anomalies
    gcm_NET_bias = NET[:,2:,:]
    obs_NET_bias = anom_obs_clisccp_dom*NETkernel_dom
    gcm_SW_bias = SW[:,2:,:]
    obs_SW_bias = anom_obs_clisccp_dom*SWkernel_dom
    gcm_LW_bias = LW[:,2:,:]
    obs_LW_bias = anom_obs_clisccp_dom*LWkernel_dom

    ## Aggregate high, mid, and low clouds over medium and thick ISCCP ranges
    CTPmids = obs_clisccp.getAxis(2)[:]
    Psec_name = ['LO','MID','HI']
    Psec_bnds = ((1100,680),(680,440),(440,10))
    Psec_dic=dict(zip(Psec_name,Psec_bnds))
    Tsec_name = ['MED','THICK']
    Tsections=[slice(0,2),slice(2,4)]
    Tsec_dic=dict(zip(Tsec_name,Tsections))
    
    agg_obs_NET_bias=np.zeros(gcm_SW_bias.shape)
    agg_gcm_NET_bias=np.zeros(gcm_SW_bias.shape)
    agg_obs_SW_bias=np.zeros(gcm_SW_bias.shape)
    agg_gcm_SW_bias=np.zeros(gcm_SW_bias.shape)
    agg_obs_LW_bias=np.zeros(gcm_SW_bias.shape)
    agg_gcm_LW_bias=np.zeros(gcm_SW_bias.shape)
    agg_obs_clisccp_bias=np.zeros(gcm_SW_bias.shape)
    agg_gcm_clisccp_bias=np.zeros(gcm_SW_bias.shape)
    
    obs_NET_bias = MV.where(obs_NET_bias.mask,0,obs_NET_bias)
    gcm_NET_bias = MV.where(gcm_NET_bias.mask,0,gcm_NET_bias)
    obs_SW_bias = MV.where(obs_SW_bias.mask,0,obs_SW_bias)
    gcm_SW_bias = MV.where(gcm_SW_bias.mask,0,gcm_SW_bias)
    obs_LW_bias = MV.where(obs_LW_bias.mask,0,obs_LW_bias)
    gcm_LW_bias = MV.where(gcm_LW_bias.mask,0,gcm_LW_bias)
    anom_obs_clisccp_dom = MV.where(anom_obs_clisccp_dom.mask,0,anom_obs_clisccp_dom)
    clisccp_bias_dom = MV.where(clisccp_bias_dom.mask,0,clisccp_bias_dom)

    tt=-1
    for Tsec in Tsec_name:
        tt+=1
        TT=Tsec_dic[Tsec]
        pp=-1
        for Psec in Psec_name:
            pbot,ptop=Psec_dic[Psec]
            PP = np.where(np.logical_and(CTPmids<=pbot, CTPmids>ptop))[0]
            if len(CTPmids[PP])>0:
                pp+=1
                agg_obs_NET_bias[:,tt,pp,:] = np.ma.sum(np.ma.sum(np.array(obs_NET_bias)[:,TT,PP,:],1),1)
                agg_gcm_NET_bias[:,tt,pp,:] = np.ma.sum(np.ma.sum(np.array(gcm_NET_bias)[:,TT,PP,:],1),1)
                agg_obs_SW_bias[:,tt,pp,:] = np.ma.sum(np.ma.sum(np.array(obs_SW_bias)[:,TT,PP,:],1),1)
                agg_gcm_SW_bias[:,tt,pp,:] = np.ma.sum(np.ma.sum(np.array(gcm_SW_bias)[:,TT,PP,:],1),1)
                agg_obs_LW_bias[:,tt,pp,:] = np.ma.sum(np.ma.sum(np.array(obs_LW_bias)[:,TT,PP,:],1),1)
                agg_gcm_LW_bias[:,tt,pp,:] = np.ma.sum(np.ma.sum(np.array(gcm_LW_bias)[:,TT,PP,:],1),1)
                agg_obs_clisccp_bias[:,tt,pp,:] = np.ma.sum(np.ma.sum(np.array(anom_obs_clisccp_dom)[:,TT,PP,:],1),1)
                agg_gcm_clisccp_bias[:,tt,pp,:] = np.ma.sum(np.ma.sum(np.array(clisccp_bias_dom)[:,TT,PP,:],1),1)
    NP = pp+1
    NT = tt+1

    ## Compute E_ctp-tau -- Cloud properties error 
    ctot1 = np.ma.sum(np.ma.sum(agg_gcm_clisccp_bias**2,1),1)/(NT*NP)
    ctot2 = np.ma.sum(np.ma.sum(agg_obs_clisccp_bias**2,1),1)/(NT*NP)

    ## Compute E_LW -- LW-relevant cloud properties error 
    ctot3 = np.ma.sum(np.ma.sum(agg_gcm_LW_bias**2,1),1)/(NT*NP)
    ctot4 = np.ma.sum(np.ma.sum(agg_obs_LW_bias**2,1),1)/(NT*NP)

    ## Compute E_SW -- SW-relevant cloud properties error 
    ctot5 = np.ma.sum(np.ma.sum(agg_gcm_SW_bias**2,1),1)/(NT*NP)
    ctot6 = np.ma.sum(np.ma.sum(agg_obs_SW_bias**2,1),1)/(NT*NP)

    ## Compute E_NET -- NET-relevant cloud properties error 
    ctot7 = np.ma.sum(np.ma.sum(agg_gcm_NET_bias**2,1),1)/(NT*NP)
    ctot8 = np.ma.sum(np.ma.sum(agg_obs_NET_bias**2,1),1)/(NT*NP)

    # compute one metric 
    E_ctpt_numer = np.ma.sqrt(np.ma.sum(WTS_dom*ctot1)) # (scalar)
    E_ctpt_denom = np.ma.sqrt(np.ma.sum(WTS_dom*ctot2)) # (scalar)
    E_LW_numer = np.ma.sqrt(np.ma.sum(WTS_dom*ctot3)) # (scalar)
    E_LW_denom = np.ma.sqrt(np.ma.sum(WTS_dom*ctot4)) # (scalar)
    E_SW_numer = np.ma.sqrt(np.ma.sum(WTS_dom*ctot5)) # (scalar)
    E_SW_denom = np.ma.sqrt(np.ma.sum(WTS_dom*ctot6)) # (scalar)
    E_NET_numer = np.ma.sqrt(np.ma.sum(WTS_dom*ctot7)) # (scalar)
    E_NET_denom = np.ma.sqrt(np.ma.sum(WTS_dom*ctot8)) # (scalar)

    E_ctpt = E_ctpt_numer/E_ctpt_denom
    E_LW = E_LW_numer/E_LW_denom
    E_SW = E_SW_numer/E_SW_denom
    E_NET = E_NET_numer/E_NET_denom

    return(E_TCA,E_ctpt,E_LW,E_SW,E_NET)

    
###########################################################################
def monthly_anomalies(data):
    """
    Compute departures from the climatological annual cycle
    usage: 
    anom,avg = monthly_anomalies(data)   
    """
    anomdata=nanarray(data.shape)
    avgdata=nanarray(data[:12].shape)
    for i in range(12):
        avgdata[i] = MV.average(data[i::12],0)
        anomdata[i::12] = data[i::12] - avgdata[i]

    try:
        avgdata.setAxisList(data[:12].getAxisList())
        anomdata.setAxisList(data.getAxisList())
    except:
        pass
    
    return (anomdata,avgdata)

###########################################################################
def nanarray(vector):
    """
    this generates a masked array with the size given by vector
    example: vector = (90,144,28)
    similar to this=NaN*ones(x,y,z) in matlab
    """

    this=MV.zeros(vector)
    this=MV.masked_where(this==0,this)

    return this
    
###########################################################################
def obscuration_feedback_terms_general(L_R_bar0,dobsc_fbk,dunobsc_fbk,dobsc_cov_fbk,Klw,Ksw):
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
    L_R_bar0 = 100*L_R_bar0
    dobsc_fbk = 100*dobsc_fbk
    dunobsc_fbk = 100*dunobsc_fbk
    dobsc_cov_fbk = 100*dobsc_cov_fbk
    
    LWdobsc_fbk = MV.sum(MV.sum(Klw_low * dobsc_fbk,1),1)
    LWdunobsc_fbk = MV.sum(MV.sum(Klw_low * dunobsc_fbk,1),1)
    LWdobsc_cov_fbk = MV.sum(MV.sum(Klw_low * dobsc_cov_fbk,1),1)    
    
    SWdobsc_fbk = MV.sum(MV.sum(Ksw_low * dobsc_fbk,1),1)
    SWdunobsc_fbk = MV.sum(MV.sum(Ksw_low * dunobsc_fbk,1),1)
    SWdobsc_cov_fbk = MV.sum(MV.sum(Ksw_low * dobsc_cov_fbk,1),1)    
    
    ###########################################################################
    # Further break down the true and apparent low cloud-induced radiation anomalies into components
    ###########################################################################
    # No need to break down dobsc_fbk, as that is purely an amount component.
        
    # Break down dunobsc_fbk:
    C_ctl = L_R_bar0
    dC = dunobsc_fbk
    C_fut = C_ctl + dC
    
    obsc_fbk_output = ZA.KT_decomposition_general(C_ctl,C_fut,Klw_low,Ksw_low)        
   
    obsc_fbk_output['LWdobsc_fbk'] = LWdobsc_fbk
    obsc_fbk_output['LWdunobsc_fbk'] = LWdunobsc_fbk
    obsc_fbk_output['LWdobsc_cov_fbk'] = LWdobsc_cov_fbk
    obsc_fbk_output['SWdobsc_fbk'] = SWdobsc_fbk
    obsc_fbk_output['SWdunobsc_fbk'] = SWdunobsc_fbk
    obsc_fbk_output['SWdobsc_cov_fbk'] = SWdobsc_cov_fbk
    
    return obsc_fbk_output
        
###########################################################################
def obscuration_terms3(c1,c2):
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
    
    AX = c2.getAxisList()
    
    c1=MV.masked_where(c2.mask,c1)
    c2=MV.masked_where(c1.mask,c2)
    
    # SPLICE c1 and c2:
    # MAKE SURE c1 and c2 are the same size!!!
    if c1.shape != c2.shape:
        raise RuntimeError('c1 and c2 are NOT the same size!!!')
        
    c12=np.ma.append(c1,c2,axis=0)    
    
    midpt=len(c1)
           
    U12 = MV.sum(MV.sum(c12[:,:,2:,:],1),1)/100.
    
    L12 = c12[:,:,:2,:]/100.  
    
    F12 = 1. - U12
    F12=MV.masked_less(F12,0)

    F12b = MV.array(np.expand_dims(np.expand_dims(F12,axis=1),axis=1))
    F12b=MV.masked_where(L12[:,:1,:1,:].mask,F12b)
    
    L_R12 = L12/F12b
    sum_L_R12 = MV.sum(MV.sum(L_R12,1),1)
    sum_L_R12b = MV.array(np.expand_dims(np.expand_dims(sum_L_R12,axis=1),axis=1))
    sum_L_R12c = np.broadcast_to(sum_L_R12b,L_R12.shape)
    this = MV.masked_outside(sum_L_R12c,0,1)
    L_R12 = MV.masked_where(this.mask,L_R12)
    
    L_R12 = MV.masked_where(sum_L_R12c>1,L_R12)
        
    L_R_prime,L_R_bar = monthly_anomalies(L_R12)
    F_prime,F_bar = monthly_anomalies(F12b)    
    L_prime,L_bar = monthly_anomalies(L12)
    
    # Cannot have negative cloud fractions:
    L_R_bar[L_R_bar<0]=0
    F_bar[F_bar<0]=0    
    
    rep_L_bar = tile_uneven(L_bar,L12)    
    rep_L_R_bar = tile_uneven(L_R_bar,L_R12)            
    rep_F_bar = tile_uneven(F_bar,F12b)
    
    # Cannot have negative cloud fractions:
    L_R_bar[L_R_bar<0]=0
    F_bar[F_bar<0]=0

    dobsc = rep_L_R_bar * F_prime
    dunobsc = L_R_prime * rep_F_bar
    prime_prime = (L_R_prime * F_prime)

    dobsc_cov,climo_prime_prime = monthly_anomalies(prime_prime)   
    
    # Re-scale these anomalies by 2, since we have computed all anomalies w.r.t. 
    # the ctl+pert average rather than w.r.t. the ctl average
    dobsc*=2
    dunobsc*=2
    dobsc_cov*=2
    
    return(rep_L_R_bar[midpt:],dobsc[midpt:],dunobsc[midpt:],dobsc_cov[midpt:])    

###########################################################################
def regional_breakdown(data,OCN,LND,area_wts,AX,norm=False):
    # Compute spatial averages over various geographical regions, for ocean, land, and both
    # if norm=False (the default), these averages are scaled by the fractional area of the planet over which they occur
    # if norm=True, these are simply area-weighted averages
    
    ocn_area_wts,lnd_area_wts = apply_land_mask_v3(area_wts,OCN,LND)
    mx = np.arange(10,101,10) # max latitude of region (i.e., from -mx to mx); last one is for Arctic
    denom = 1
    reg_dict = {}
    sections=list(data.keys())
    surfaces=['all','ocn','lnd']
    for r in mx:
        if r==100:
            region = 'Arctic'
            domain = cdutil.region.domain(latitude = (70,90))
        else:
            region = 'eq'+str(r)
            domain = cdutil.region.domain(latitude = (-r,r))
        reg_dict[region]={}
        for sfc in surfaces:    
            reg_dict[region][sfc]={}       
            for sec in sections:
                reg_dict[region][sfc][sec] = {}
                DATA = data[sec]
                names=list(DATA.keys())
                for name in names:
                    #reg_dict[region][sfc][sec][name] = {}
                    fbk = DATA[name]
                    fbk.setAxisList(AX)
                    ocn_fbk,lnd_fbk = apply_land_mask_v3(fbk,OCN,LND)
                    if sfc=='ocn':
                        wtd_fbk = np.ma.sum(np.ma.sum(domain.select(ocn_fbk*area_wts),1),1)
                        if norm:
                            denom = np.ma.sum(np.ma.sum(domain.select(ocn_area_wts),1),1)                             
                    elif sfc=='lnd':
                        wtd_fbk = np.ma.sum(np.ma.sum(domain.select(lnd_fbk*area_wts),1),1)
                        if norm:
                            denom = np.ma.sum(np.ma.sum(domain.select(lnd_area_wts),1),1)
                    elif sfc=='all':
                        wtd_fbk = np.ma.sum(np.ma.sum(domain.select(    fbk*area_wts),1),1)
                        if norm:
                            denom = np.ma.sum(np.ma.sum(domain.select(area_wts),1),1)                        
                    wtd_fbk = wtd_fbk/denom
                    reg_dict[region][sfc][sec][name] = np.ma.average(wtd_fbk,0)
                    
    # reserve spots in the dictionary for asc/dsc feedbacks                    
    reg_dict['eq30']['ocn_asc']={}
    reg_dict['eq30']['ocn_dsc']={}
    for sec in sections:
        reg_dict['eq30']['ocn_asc'][sec]={}
        reg_dict['eq30']['ocn_dsc'][sec]={}
        
    return(reg_dict)    
        
###########################################################################
def select_regions(field,region):
    if region == 'eq90':
        inds=np.where((np.abs(lats[:])<90))
    elif region=='eq60':
        inds=np.where((np.abs(lats[:])<60))
    elif region=='eq30':
        inds=np.where((np.abs(lats[:])<30))
    elif region=='30-60':
        inds=np.where((np.abs(lats[:])<60) & (np.abs(lats[:])>30))
    elif region=='30-80':
        inds=np.where((np.abs(lats[:])<80) & (np.abs(lats[:])>30))
    elif region=='40-70':
        inds=np.where((np.abs(lats[:])<70) & (np.abs(lats[:])>40))
    elif region=='Arctic':
        inds=np.where((lats[:]>70))
    field_dom = MV.take(field, inds[0], axis=-2)
    return(field_dom)
    
###########################################################################
def tile_uneven(data,data_to_match):
    """extend data to match size of data_to_match even if not a multiple of 12"""
    
    A12=len(data_to_match)//12
    ind=np.arange(12,)
    rep_ind = np.tile(ind,(A12+1))[:int(len(data_to_match))] # int() added for python3
    
    rep_data = MV.array(np.array(data)[rep_ind]) 
    
    return rep_data    
    
###########################################################################
def YEAR(data):
    """
    Compute annual means without forcing it to be Jan through Dec
    """
    
    A=data.shape[0]
    anndata0=nanarray(data.shape)
    cnt=-1
    for i in np.arange(0,A,12):
        if len(data[i:i+12])==12: # only take full 12-month periods
            cnt+=1
            anndata0[cnt] = MV.average(data[i:i+12],0)
    B=cnt+1
    anndata = anndata0[:B]
    if type(anndata)!=float:
        anndata.setAxisList(data[:B*12:12].getAxisList())
    
    return anndata

###############################################################################################
def CloudRadKernel(filenames):

    print('Load in data')
    ctl_clisccp,fut_clisccp,LWK,SWK,dTs,ctl_clisccp_wap,fut_clisccp_wap,LWK_wap,SWK_wap,ctl_N,fut_N = get_CRK_data(filenames)
       
    # Create a dummy variable so we don't have keep calling the land mask function:
    dummy = ctl_clisccp[:12,0,0,:] # 12,90,144
    OCN,LND = apply_land_mask_v2(dummy)
    area_wts = get_area_wts(ctl_clisccp[:12,0,0,:]) # summing this over lat and lon = 1
    
    print('Compute Klein et al error metrics')
    ###########################################################################
    # Compute Klein et al cloud error metrics and their breakdown into components
    ###########################################################################  
    KEM_dict = do_klein_calcs(ctl_clisccp,LWK,SWK,obs_clisccp_AC,ctl_clisccp_wap,LWK_wap,SWK_wap,obs_clisccp_AC_wap,obs_N_AC_wap)
    # [sec][flavor][region][all / ocn / lnd / ocn_asc / ocn_dsc]

    print('Compute feedbacks')
    ###########################################################################
    # Compute cloud feedbacks and their breakdown into components
    ###########################################################################         
    clisccp_fbk,clisccp_base = compute_fbk(ctl_clisccp,fut_clisccp,dTs)       
    dummy,LWK_base = compute_fbk(LWK,LWK,dTs) 
    dummy,SWK_base = compute_fbk(SWK,SWK,dTs)    
    
    AX = ctl_clisccp[:12,0,0,:].getAxisList()             


    # The following performs the amount/altitude/optical depth decomposition of
    # Zelinka et al., J Climate (2012b), as modified in Zelinka et al., J. Climate (2013)  
    output={}  
    output_wap={}  
    for sec in sections:
        print('    for section '+sec)
        # [sec][flavor][region][all / ocn / lnd / ocn_asc / ocn_dsc]       
        
        PP=sec_dic[sec]   

        C1 = clisccp_base[:,:,PP,:]
        C2 = C1 + clisccp_fbk[:,:,PP,:]
        Klw = LWK_base[:,:,PP,:]
        Ksw = SWK_base[:,:,PP,:]
       
        output[sec] = ZA.KT_decomposition_general(C1,C2,Klw,Ksw)
    
        dummy,LWK_wap_base = compute_fbk(LWK_wap,LWK_wap,dTs) 
        dummy,SWK_wap_base = compute_fbk(SWK_wap,SWK_wap,dTs)    

        Klw = LWK_wap_base[:,:,PP,:-1] # ignore the land bin
        Ksw = SWK_wap_base[:,:,PP,:-1]
        C1 = ctl_clisccp_wap[:,:,PP,:-1]
        C2 = fut_clisccp_wap[:,:,PP,:-1]
        N1 = ctl_N[:,:-1]
        N2 = fut_N[:,:-1]
        
        # no breakdown (this is identical to within + between + covariance)
        C1b = np.moveaxis(np.moveaxis(C1,1,0),2,1)  # [TAU,CTP,month,regime]
        C1N1 = np.moveaxis(C1b*N1,2,0)              # [month,TAU,CTP,regime]
        C2b = np.moveaxis(np.moveaxis(C2,1,0),2,1)  # [TAU,CTP,month,regime]
        C2N2 = np.moveaxis(C2b*N2,2,0)              # [month,TAU,CTP,regime]
        pert,C_base = compute_fbk(C1N1,C2N2,dTs) 
        output_wap[sec] = ZA.KT_decomposition_general(C_base, C_base+pert, Klw, Ksw)

    # end for sec in sections  
    
                                            
    
    ###########################################################################
    # Compute obscuration feedback components
    ###########################################################################  
    sec='LO680' # this should already be true, but just in case...
    PP=sec_dic[sec]  
    PP=sec_dic[sec]   
    print('Get Obscuration Terms')
    CTL,FUT = ctl_clisccp,fut_clisccp
    LWK = LWK_base[:,:,PP,:]
    SWK = SWK_base[:,:,PP,:]
    obsc_output={}
    obsc_output[sec] = do_obscuration_calcs(CTL,FUT,LWK,SWK,dTs)
    
    # Do this for the omega-regimes too:
    C1 = np.moveaxis(ctl_clisccp_wap,0,-1)
    N1 = np.moveaxis(ctl_N,0,-1)
    CTL = np.moveaxis(C1*N1,-1,0)[...,:-1] # ignore the land bin
    C2 = np.moveaxis(fut_clisccp_wap,0,-1)
    N2 = np.moveaxis(fut_N,0,-1)
    FUT = np.moveaxis(C2*N2,-1,0)[...,:-1] # ignore the land bin
    LWK = LWK_wap_base[:,:,PP,:-1] # ignore the land bin
    SWK = SWK_wap_base[:,:,PP,:-1] # ignore the land bin
    obsc_output_wap={}
    obsc_output_wap[sec] = do_obscuration_calcs(CTL,FUT,LWK,SWK,dTs)           

    
    ###########################################################################
    # Compute regional averages (weighted by fraction of globe); place in dictionary
    ########################################################################### 
    print('Compute regional averages') 
    # [region][sfc][sec][name] 
    obsc_fbk_dict = regional_breakdown(obsc_output,OCN,LND,area_wts,AX)
    fbk_dict = regional_breakdown(output,OCN,LND,area_wts,AX)   
    
    # Put all the ascending and descending region quantities in a dictionary
    names=list(output_wap['ALL'].keys())
    for sec in sections:
        for name in names:
            fbk_dict['eq30']['ocn_asc'][sec][name] = np.ma.average(np.sum((output_wap[sec][name])[:,:cutoff],1),0)
            fbk_dict['eq30']['ocn_dsc'][sec][name] = np.ma.average(np.sum((output_wap[sec][name])[:,cutoff:],1),0)  
              
    sec='LO680'
    names=list(obsc_output_wap[sec].keys())
    for name in names:
        obsc_fbk_dict['eq30']['ocn_asc'][sec][name] = np.ma.average(np.sum((obsc_output_wap[sec][name])[:,:cutoff],1),0)
        obsc_fbk_dict['eq30']['ocn_dsc'][sec][name] = np.ma.average(np.sum((obsc_output_wap[sec][name])[:,cutoff:],1),0)  
        
    meta = {
    "date_modified" :   str(date.today()),
    "author"        :   "Mark D. Zelinka <zelinka1@llnl.gov>",
    }
    fbk_dict['metadata'] = meta
    obsc_fbk_dict['metadata'] = meta

    # [sec][flavor][region][all / ocn / lnd / ocn_asc / ocn_dsc]
    return(fbk_dict,obsc_fbk_dict,KEM_dict)
        
    
