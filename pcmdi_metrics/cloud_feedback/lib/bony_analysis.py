import cdutil
import numpy as np
import MV2 as MV

###############################################################################################
def bony_sorting_part1(w500,binedges):

    A,B,C = w500.shape
    dx=np.diff(binedges)[0]
    # Compute composite:    
    OKwaps=nanarray((A,B,C,2+len(binedges))) # add 2 for the exceedances
    xx=0
    for x in binedges:
        xx+=1
        w500_bin=MV.masked_less(w500,x)
        OKwaps[...,xx]=MV.masked_greater_equal(w500_bin,x+dx)

    # do the first wap bin:
    OKwaps[...,0]=MV.masked_greater_equal(w500,binedges[0])
    # do the last wap bin:
    OKwaps[...,-1]=MV.masked_less(w500,binedges[-1]+dx)

    return OKwaps   # [month,lat,lon,wapbin]

###############################################################################################
def bony_sorting_part2(OKwaps,data,OKland,WTS,binedges):

    binary_waps = MV.where(OKwaps.mask,0,1) # zeros and ones
    binary_land = MV.where(OKland.mask,0,1) # zeros and ones
    if np.ndim(data.mask)==0:
        binary_data = MV.array(np.ones(data.shape))
    else:
        binary_data = MV.where(data.mask,0,1) # zeros and ones
    
    # this function maps data from [time,...?,lat,lon] to [time,...?,wapbin]
    sh = list(data.shape[:-2])
    sh.append(3+len(binedges)) # add 2 for the exceedances, 1 for land
    DATA = nanarray((sh)) # add 2 for the exceedances, 1 for land
    DATA = np.moveaxis(np.moveaxis(DATA,0,-1),-2,0)
    
    sh = list()
    sh = np.append(data.shape[0],3+len(binedges)) # add 2 for the exceedances, 1 for land
    CNTS = nanarray((sh[-1::-1])) # add 2 for the exceedances, 1 for land
    
    binary_waps2 = np.moveaxis(binary_waps,-1,0) # bring the wap bins to index 0  
    A1b = np.moveaxis(np.moveaxis(binary_waps2*WTS,0,-1),0,-1) # zero for wap outside range, frac area for wap inside range
    CNTS[:-1,:] = np.sum(np.sum(A1b,-3),-3) # fractional area of this bin includes regions where data is undefined
    
    # reshape stuff to be [...?,lat,lon,time] to capitalize on broadcasting
    WTS2 = np.moveaxis(WTS,0,-1)
    binary_data2 = np.moveaxis(binary_data,0,-1)
    data2 = np.moveaxis(data,0,-1) 
    for xx in range(2+len(binedges)):
        A2 = binary_data2*A1b[...,xx,:] # zero for wap outside range or undefined data, frac area for wap inside range
        denom = np.ma.sum(np.ma.sum(A2,-2),-2)
        numer = np.sum(np.sum(data2*A2,-2),-2)
        DATA[xx,:] = numer/denom # bin-avg data is computed where both data and wap are defined        
            
    # now do the land-only average:
    A1b = np.moveaxis(binary_land*WTS,0,-1)  # zero for ocean points, frac area for land points
    CNTS[-1,:] = np.sum(np.sum(A1b,-2),-2) # fractional area of this bin includes regions where data is undefined   
    A2 = binary_data2*A1b # zero for ocean points or undefined data, frac area for land points
    denom = np.ma.sum(np.ma.sum(A2,-2),-2)
    numer = np.sum(np.sum(data2*A2,-2),-2)
    DATA[-1,:] = numer/denom # bin-avg data is computed where both data and wap are defined        

    # Ensure that the area matrix has zeros rather than masked points
    CNTS[CNTS.mask]=0
    
    if np.allclose(0.5,np.sum(CNTS,0))==False:
        print('sum of fractional counts over all wapbins does not equal 0.5 (tropical fraction)')
        moot
        
    # DATA contains area-weighted averages within each bin
    # CNTS contains fractional areas represented by each bin
    # so summing (DATA*CNTS) over all regimes should recover the tropical contribution to the global mean
    DATA2 = np.moveaxis(DATA,0,-1)
    CNTS2 = np.moveaxis(CNTS,0,-1)
    v1 = np.moveaxis(np.sum(DATA2*CNTS2,-1),-1,0)
    v2a = 0.5*cdutil.averager(data, axis='xy', weights='weighted')
    v2b = np.moveaxis(np.ma.sum(np.ma.sum(WTS2*data2,-2),-2),-1,0)
    
    if np.allclose(v1,v2a)==False or np.allclose(v1,v2b)==False:
        print('Cannot reconstruct tropical average via summing regimes')
            
    DATA3 = np.moveaxis(np.moveaxis(DATA,0,-1),-2,0)
    
    return DATA3,CNTS2 #[time,wapbin]

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

