import numpy as np
import MV2 as MV

###########################################################################
def map_SWkern_to_lon(Ksw,albcsmap):
    """
    Map each location's clear-sky surface albedo to the correct albedo bin
    """

    albcsmap=MV.masked_greater(albcsmap,1.0)
    albcsmap=MV.masked_less(albcsmap,0.0)
    from scipy.interpolate import interp1d
    # Ksw is size 12,7,7,lats,3
    # albcsmap is size A,lats,lons
    albcs=np.arange(0.0,1.5,0.5) 
    A=albcsmap.shape[0]
    TT=Ksw.shape[1]
    PP=Ksw.shape[2]
    lenlat=Ksw.shape[3]
    lenlon=albcsmap.shape[2]
    SWkernel_map = MV.zeros((A,TT,PP,lenlat,lenlon))
    SWkernel_map = MV.masked_where(SWkernel_map==0,SWkernel_map)
    
    for M in range(A):
        MM=M
        while MM>11:
            MM=MM-12
        for LA in range(lenlat):
            alon=albcsmap[M,LA,:] 
            # interp1d can't handle mask but it can deal with NaN (?)
            try:
                alon2=MV.where(alon.mask,np.nan,alon)   
            except:
                alon2=alon
            if np.ma.count(alon2)>1: # at least 1 unmasked value
                if len(np.where(Ksw[MM,:,:,LA,:]>0))==0:
                    SWkernel_map[M,:,:,LA,:] = 0
                else:
                    f = interp1d(albcs,Ksw[MM,:,:,LA,:],axis=2)
                    ynew = f(alon2.data)
                    ynew=MV.masked_where(alon2.mask,ynew)
                    SWkernel_map[M,:,:,LA,:] = ynew
            else:
                continue


    return SWkernel_map

###########################################################################
def KT_decomposition_general(c1,c2,Klw,Ksw):
    """
    this function takes in a (month,TAU,CTP,lat,lon) matrix and performs the 
    decomposition of Zelinka et al 2013 doi:10.1175/JCLI-D-12-00555.1
    """

    
    # To help with broadcasting, move month axis to the end so that TAU,CTP are first
    c1 = np.array(np.moveaxis(c1,0,-1))
    c2 = np.array(np.moveaxis(c2,0,-1))
    Klw = np.moveaxis(Klw,0,-1)
    Ksw = np.moveaxis(Ksw,0,-1)
    
    sum_c=np.ma.sum(np.ma.sum(c1,0),0)                              # Eq. B2
    dc = c2-c1 
    sum_dc=np.ma.sum(np.ma.sum(dc,0),0)
    dc_prop = c1*(sum_dc/sum_c)
    dc_star = dc - dc_prop                                          # Eq. B1

    # LW components
    Klw0 = np.ma.sum(np.ma.sum(Klw*c1/sum_c,0),0)                   # Eq. B4
    Klw_prime = Klw - Klw0                                          # Eq. B3
    B7a = np.ma.sum(c1/sum_c,1,keepdims=True)                       # need to keep this as [TAU,1,...]
    Klw_p_prime = np.ma.sum(Klw_prime*B7a,0)                        # Eq. B7
    Klw_t_prime = np.ma.sum(Klw_prime*np.ma.sum(c1/sum_c,0),1)      # Eq. B8   
    Klw_resid_prime = Klw_prime - np.expand_dims(Klw_p_prime,0) - np.expand_dims(Klw_t_prime,1)        # Eq. B9
    dRlw_true = np.ma.sum(np.ma.sum(Klw*dc,1),0)                    # LW total
    dRlw_prop = Klw0*sum_dc                                         # LW amount component
    dRlw_dctp = np.ma.sum(Klw_p_prime*np.ma.sum(dc_star,0),0)       # LW altitude component
    dRlw_dtau = np.ma.sum(Klw_t_prime*np.ma.sum(dc_star,1),0)       # LW optical depth component
    dRlw_resid = np.ma.sum(np.ma.sum(Klw_resid_prime*dc_star,1),0)  # LW residual
    dRlw_sum = dRlw_prop + dRlw_dctp + dRlw_dtau + dRlw_resid       # sum of LW components -- should equal LW total

    # SW components
    Ksw0 = np.ma.sum(np.ma.sum(Ksw*c1/sum_c,0),0)                   # Eq. B4
    Ksw_prime = Ksw - Ksw0                                          # Eq. B3
    B7a = np.ma.sum(c1/sum_c,1,keepdims=True)                       # need to keep this as [TAU,1,...]
    Ksw_p_prime = np.ma.sum(Ksw_prime*B7a,0)                        # Eq. B7
    Ksw_t_prime = np.ma.sum(Ksw_prime*np.ma.sum(c1/sum_c,0),1)      # Eq. B8  
    Ksw_resid_prime = Ksw_prime - np.expand_dims(Ksw_p_prime,0) - np.expand_dims(Ksw_t_prime,1)        # Eq. B9 
    dRsw_true = np.ma.sum(np.ma.sum(Ksw*dc,1),0)                    # SW total
    dRsw_prop = Ksw0*sum_dc                                         # SW amount component
    dRsw_dctp = np.ma.sum(Ksw_p_prime*np.ma.sum(dc_star,0),0)       # SW altitude component
    dRsw_dtau = np.ma.sum(Ksw_t_prime*np.ma.sum(dc_star,1),0)       # SW optical depth component
    dRsw_resid = np.ma.sum(np.ma.sum(Ksw_resid_prime*dc_star,1),0)  # SW residual
    dRsw_sum = dRsw_prop + dRsw_dctp + dRsw_dtau + dRsw_resid       # sum of SW components -- should equal SW total

    # Set SW fields to zero where the sun is down
    RR = Ksw0.mask
    dRsw_true = MV.where(RR,0,dRsw_true)
    dRsw_prop = MV.where(RR,0,dRsw_prop)
    dRsw_dctp = MV.where(RR,0,dRsw_dctp)
    dRsw_dtau = MV.where(RR,0,dRsw_dtau)
    dRsw_resid = MV.where(RR,0,dRsw_resid)

    # Move month axis back to the beginning
    output={}
    output['LWcld_tot'] = MV.array(np.moveaxis(dRlw_true,-1,0))
    output['LWcld_amt'] = MV.array(np.moveaxis(dRlw_prop,-1,0))
    output['LWcld_alt'] = MV.array(np.moveaxis(dRlw_dctp,-1,0))
    output['LWcld_tau'] = MV.array(np.moveaxis(dRlw_dtau,-1,0))
    output['LWcld_err'] = MV.array(np.moveaxis(dRlw_resid,-1,0))
    output['SWcld_tot'] = MV.array(np.moveaxis(dRsw_true,-1,0))
    output['SWcld_amt'] = MV.array(np.moveaxis(dRsw_prop,-1,0))
    output['SWcld_alt'] = MV.array(np.moveaxis(dRsw_dctp,-1,0))
    output['SWcld_tau'] = MV.array(np.moveaxis(dRsw_dtau,-1,0))
    output['SWcld_err'] = MV.array(np.moveaxis(dRsw_resid,-1,0))
    #output['dc_star'] = MV.array(np.moveaxis(dc_star,-1,0))
    #output['dc_prop'] = MV.array(np.moveaxis(dc_prop,-1,0))    
    
    return output
