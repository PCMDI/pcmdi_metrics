#!/usr/bin/env cdat
"""
Use Gregory approach to estimate ECS
"""

#IMPORT STUFF:
#=====================
import numpy as np
from scipy import stats
import cdms2
import cdtime
import cdutil
import MV2

###########################################################################
def get_anom_abrupt(ab_path,pi_path,var):
    """
    this function returns the array of var values with 
    PI-control 21 yr running mean-smoothed values from
    coincident times removed (to deal with drift not removed
    from the ctl simulation which is ostensibly also happening
    in the forced runs.
    """
    
    f = cdms2.open(ab_path)

    # Get info about branch times, etc.
    source = ab_path.split('/')[-1].split('.')[1]
    if source=='GFDL-CM4':
        branch_time_in_parent = 91250 # https://errata.es-doc.org/static/view.html?uid=2f6b5963-f87e-b2df-a5b0-2f12b6b68d32        
    else: 
        branch_time_in_parent = np.float(f.branch_time_in_parent)
    branch_time_in_child = f.branch_time_in_child
    parent_time_units = f.parent_time_units
    child_time_units = f[var].getTime().units
    ab_st = f.branch_time_in_child
    
    # FOR NOW WE ONLY WANT UP TO 150 YEARS OF ABRUPT SIMULATION:
    r = cdtime.reltime(ab_st,child_time_units)
    FN = r.add(12*150,cdtime.Months) # add 121 rather than 120 because it uses day 1 rather than day 15
    ab_fn = FN.value  
              
    # Get abrupt data
    data = f(var,time=(ab_st,ab_fn)) 
    f.close()

    # Determine the appropriate overlapping piControl period               
    true_st = branch_time_in_parent 
    true_fn = true_st + data.getTime()[-1]
    r = cdtime.reltime(true_fn,parent_time_units)  
    true_fn = r.add(15,cdtime.Days).value # add 15 days on to take it to the end of the month
    
    # we want to grab data starting 10 yrs prior to true_st
    r = cdtime.reltime(true_st,parent_time_units)
    extend_st = r.sub(120,cdtime.Months).value
    # we want to grab data ending 10 yrs beyond to true_fn
    r = cdtime.reltime(true_fn,parent_time_units)
    extend_fn = r.add(121,cdtime.Months).value # add 121 rather than 120 because it uses day 1 rather than day 15
        
    # Get the smoothed piControl data
    pi_data_smooth = get_smooth(var,pi_path,extend_st,extend_fn,true_st,true_fn)
    
    # Compute the anomaly
    LA = len(data)
    LP = len(pi_data_smooth)
    endpt = np.min((LA,LP,150*12))  # take no data beyond year 150
    anom = data[:endpt,:] - pi_data_smooth[:endpt,:]
    anom.setAxisList(data[:endpt,:].getAxisList())        
    cdutil.setTimeBoundsMonthly(anom)          
    
    return anom
###########################################################################


###########################################################################
def get_smooth(var,pi_xml,extend_st,extend_fn,true_st,true_fn):
    
    f=cdms2.open(pi_xml)    
    pi_data = f(var,time=(extend_st,extend_fn))
    f.close() 
                       
    # Compute 21-yr running mean
    avgpi_data = running_mean(pi_data,21)
    
    # Now just hang onto portion of piControl that overlaps with abrupt
    pi_data_smooth = avgpi_data.subRegion(time=(true_st,true_fn))
    
    return pi_data_smooth
    
def global_avg(DATA):
    GLavg_DATA = cdutil.averager(DATA, axis="xy", weights='weighted')       
    return GLavg_DATA
###########################################################################
    
    
###########################################################################
def annual_avg(data):
    """
    Compute annual means without forcing it to be Jan through Dec
    """
    
    A=data.shape[0]
    anndata0=np.empty(data.shape)
    anndata0[:] = np.nan
    cnt=-1
    for i in np.arange(0,A,12):
        try:
            LD = len(data[i:i+12])
        except:
            continue
        if LD==12: # only take full 12-month periods
            cnt+=1
            anndata0[cnt] = np.ma.average(data[i:i+12],0)

    B=cnt+1
    anndata = MV2.array(anndata0[:B]) # convert to a cdms2 transient variable
    if type(anndata)!=float:
        anndata.setAxisList(data[:B*12:12].getAxisList())
    
    return anndata
###########################################################################

###########################################################################
def running_mean(data,N):

    # Compute N-yr running mean
    back = N/2
    forward = N/2+1
    avgdata = np.empty(data.shape)
    avgdata[:] = np.nan
    for month in range(12):
        subset = data[month::12,:]
        avgsubset=np.empty(subset.shape)
        avgsubset[:] = np.nan
        LS=len(subset)
        for ii in range(LS):
            start = np.max((ii-back,0))
            finish = np.min((ii+forward,LS))
            avgsubset[ii,:] = np.ma.average(subset[int(start):int(finish),:],0)
        avgdata[month::12,:] = avgsubset
        
    avgdata = MV2.array(avgdata) # convert to a cdms2 transient variable
    avgdata.setAxisList(data.getAxisList())
    
    return avgdata
###########################################################################
    
def compute_ECS(filenames):
    data={}
    fields = ['tas', 'rlut', 'rsut', 'rsdt'] # needed for Gregory plots
    for var in fields:
        ab_path = filenames['abrupt-4xCO2'][var]
        pi_path = filenames['piControl'][var]
        ab_anom = get_anom_abrupt(ab_path,pi_path,var) 
        # globally and annually average:
        data[var] = annual_avg(global_avg(ab_anom))               
        
    rndt = data['rsdt'] - data['rsut'] - data['rlut']
    tas = data['tas']
    
    scale = np.log2(4.0)
    x = tas[:150]
    y = rndt[:150]
    m, b, r, p, std_err = stats.linregress(x,y)
    ERF150 = b/scale
    LAM150 = m
    ecs = -ERF150/LAM150
    
    return ecs
