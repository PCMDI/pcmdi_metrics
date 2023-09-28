# Compute ECS, ERF, and lambda from abrupt-4xCO2 experiments via Gregory approach

import xarray as xr
import xcdat
import numpy as np
from scipy import stats
import cftime

def dict_to_dataset(DICT):
    # Convert a dictionary of Datasets to a single Dataset
    data_vars={}
    for var in list(DICT.keys()):
        data_vars[var] = (["year"], DICT[var][var].data)
    ds = xr.Dataset(
        data_vars,
        coords=dict(year=DICT[var].year),
    )
    return(ds)

def get_branch_time(pi,ab):
    # Determine when abrupt overlaps with piControl
    # returns the following:
    # 1) st: the branch time in cftime.datetime format
    # 2) fn: the last abrupt year in cftime.datetime format
    # 3) extensions beyond the ~150-year overlap period to allow for 21-year rolling mean:
    #    3a) extend_st -- the date 10 years prior to st
    #    3b) extend_fn -- the date 10 years after fn
    
    var = ab.variable_id
    source = ab.source_id
    experiment = ab.experiment_id
    absub = ab.isel(time=slice(0,12*150))
    lenab = int(absub[var].shape[0]/12)-1
    btip = int(absub.attrs['branch_time_in_parent']) # timestep, not a date

    if source=='GFDL-CM4' and (experiment=='1pctCO2' or experiment=='abrupt-4xCO2' or experiment=='historical'): 
        btip = 91250 # https://errata.es-doc.org/static/view.html?uid=2f6b5963-f87e-b2df-a5b0-2f12b6b68d32    
    ptu = absub.attrs['parent_time_units']
    # print('  branch time in parent:   '+str(btip)+' '+ptu)
    # print('  parent times:   '+str(pi.time.dt.year[0].values)+' - '+str(pi.time.dt.year[-1].values))
    start = int(ptu.split(' ')[2][:4])
    cal = pi.time.dt.calendar
    # see http://cfconventions.org/cf-conventions/cf-conventions.html#calendar
    if cal=='360_day':
        dpy=360
    elif cal=='noleap':
        dpy=365
    elif cal=='proleptic_gregorian' or cal=='standard' or cal=='julian':
        dpy=365.25
    else:
        raise(Exception('Not sure how to handle '+cal+' calendar'))
    if source=='CIESM' and (experiment=='abrupt-4xCO2' or experiment=='1pctCO2'):
        # info from Yi Qin 10/1/20:
        # "The branch_time for 4xCO2 should be the 101-yr of these published 500-yr piControl data, 
        # but I wrongly regarded the “raw” piControl with piControl-spinup as the parent_case, which is a 1000-yr long run.
        year0 = 101 
    elif source=='KACE-1-0-G' and (experiment=='abrupt-4xCO2' or experiment=='1pctCO2'):
        # info from Jae-Hee Lee (via Gavin Schmidt on 1/26/22):
        # "We used year 2150 of piControl as the initial condition for the KACE-1-0-G 1pctCO2 runs. 
        # so, you can assume that 1850 in the 1pctCO2 and 2150 in the piControl are the same
        year0 = 2150         
    else:
        year0 = int((btip/dpy)+start)
    year150 = int(year0+lenab)
    st=cftime.datetime(year0, 1, 1).strftime("%Y-%m-%dT%H:%M:%S")
    fn=cftime.datetime(year150, 12, 31,23,59,59).strftime("%Y-%m-%dT%H:%M:%S")
    # Add on 10 years before st and after fn to assist in computing 21-year rolling means
    extend_st=cftime.datetime(np.max((year0-10,1)), 1, 1).strftime("%Y-%m-%dT%H:%M:%S")
    extend_fn=cftime.datetime(year150+10, 12, pi.time.dt.day[-1],23,59,59).strftime("%Y-%m-%dT%H:%M:%S") 

    return(extend_st,extend_fn,st,fn)#,year0,year150)

def get_data(pi,ab):  
    # Return the piControl running mean and the abrupt deviation from this

    var=ab.variable_id
    extend_st,extend_fn,st,fn = get_branch_time(pi,ab)
    absub = ab.isel(time=slice(0,12*150))
    pisub = pi.sel(time=slice(extend_st,extend_fn))
    if len(pisub.time)<1200:
        print('len(time)<1200...skipping')
        return None

    bdate = pisub.time.dt.year.values 
    # compute global means:
    GLcntl = pisub.spatial.average(var)
    GLpert = absub.spatial.average(var)
    # compute annual means:
    annpert = GLpert.groupby('time.year').mean('time')
    anncntl = GLcntl.groupby('time.year').mean('time')
    # compute 21-year centered rolling mean:
    runcntl = anncntl.rolling(year = 21, min_periods = 1, center = True).mean()
    # subset the rolling mean for the actual overlapping time:
    runcntlsub = runcntl.sel(year=slice(int(st[:4]),int(fn[:4])))
    # set the abrupt run's year coord to match the overlapping piCon's year coord
    annpert=annpert.assign_coords(year=runcntlsub.coords['year'])
    # compute abrupt anomalies from piControl running mean:
    annanom = annpert - runcntlsub
    
    return(runcntl,annanom)

def compute_abrupt_anoms(pifilepath,abfilepath):
    # compute annual- anad global-mean tas and EEI anomalies in abrupt4xCO2 w.r.t. piControl climo, then compute ERF, lambda, and ECS via Gregory
    cntl={}
    anom={}
    skip=False
    variables = list(pifilepath.keys())
    for var in variables:
        pi=xcdat.open_mfdataset(pifilepath[var], use_cftime = True)
        ab=xcdat.open_mfdataset(abfilepath[var], use_cftime = True)
        
        if len(ab.time)<140*12:
            print('   len(ab.time)<140*12')
            skip=True
            break
        output = get_data(pi,ab)
        if output:
            cntl[var],anom[var] = output
        else:
            skip=True
            break
    if skip:
        # print('Skipping this model...')
        return None

    CNTL = dict_to_dataset(cntl)
    ANOM = dict_to_dataset(anom)

    CNTL['eei'] = CNTL['rsdt']-CNTL['rsut']-CNTL['rlut']
    ANOM['eei'] = ANOM['rsdt']-ANOM['rsut']-ANOM['rlut']

    x = ANOM['tas'].load()
    y = ANOM['eei'].load()

    return(x,y)

def gregory_calcs(x,y):
    m, b, r, p, std_err = stats.linregress(x,y)
    ERF = b/2
    lam = m
    ECS = -ERF/lam
    return (ERF,lam,ECS)

