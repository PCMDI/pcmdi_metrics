def calcrainmetrics(pdistin,bincrates):
    ### This calculation can be applied to rain amount or rain frequency distributions 
    ### Here we'll do it for a distribution averaged over a region, but you could also do it at each grid point
    pdist=np.copy(pdistin)
    tile=np.array(0.1) # this is the threshold, 10% of rain amount or rain frequency
    pdist[0]=0 # If this is frequency, get rid of the dry frequency. If it's amount, it should already be zero or close to it.
    pmax=pdist.max()
    if pmax>0:
        imax=np.nonzero(pdist==pmax)
        rmax=np.interp(imax,range(0,len(bincrates)),bincrates)
        rainpeak=rmax[0][0]
        ### we're going to find the width by summing downward from pmax to lines at different heights, and then interpolating to figure out the rain rates that intersect the line. 
        theps=np.linspace(0.1,.99,99)*pmax
        thefrac=np.empty(theps.shape)
        for i in range(len(theps)):
            thisp=theps[i]
            overp=(pdist-thisp)*(pdist> thisp);
            thefrac[i]=sum(overp)/sum(pdist)
        ptilerain=np.interp(-tile,-thefrac,theps)
        #ptilerain/db ### check this against rain amount plot
        #ptilerain*100/db ### check this against rain frequency plot
        diffraintile=(pdist-ptilerain);
        alli=np.nonzero(diffraintile>0)
        afterfirst=alli[0][0]
        noistart=np.nonzero(diffraintile[0:afterfirst]<0)
        beforefirst=noistart[0][len(noistart[0])-1]
        incinds=range(beforefirst,afterfirst+1)
        ### need error handling on these for when inter doesn't behave well and there are multiple crossings
        if np.all(np.diff(diffraintile[incinds]) > 0):
            r1=np.interp(0,diffraintile[incinds],incinds) # this is ideally what happens. note: r1 is a bin index, not a rain rate. 
        else:
            r1=np.average(incinds) # in case interp won't return something meaningful, we use this kluge. 
        beforelast=alli[0][len(alli[0])-1]
        noiend=np.nonzero(diffraintile[beforelast:(len(diffraintile)-1)]<0)+beforelast
        afterlast=noiend[0][0]
        decinds=range(beforelast,afterlast+1)
        if np.all(np.diff(-diffraintile[decinds]) > 0):
            r2=np.interp(0,-diffraintile[decinds],decinds)
        else:
            r2=np.average(decinds)
        ### Bin width - needed to normalize the rain amount distribution                                                                                                                
        db=(bincrates[2]-bincrates[1])/bincrates[1];
        rainwidth=(r2-r1)*db+1
        return rainpeak,rainwidth,(imax[0][0],pmax),(r1,r2,ptilerain)
    else:
        return 0,0,(0,pmax),(0,0,0)

def makedists(pdata,binl):
    ##### This is called from within makeraindist.
    ##### Caclulate distributions 
    pds=pdata.shape;    nlat=pds[1];    nlon=pds[0];    nd=pds[2]
    bins=np.append(0,binl)
    n=np.empty((nlon,nlat,len(binl)))
    binno=np.empty(pdata.shape)
    for ilon in range(nlon):
        for ilat in range(nlat):
            # this is the histogram - we'll get frequency from this
            thisn,thisbin=np.histogram(pdata[ilon,ilat,:],bins)
            n[ilon,ilat,:]=thisn
            # these are the bin locations. we'll use these for the amount dist
            binno[ilon,ilat,:]=np.digitize(pdata[ilon,ilat,:],bins)
    #### Calculate the number of days with non-missing data, for normalization
    ndmat=np.tile(np.expand_dims(np.nansum(n,axis=2),axis=2),(1,1,len(bins)-1))
    thisppdfmap=n/ndmat
    #### Iterate back over the bins and add up all the precip - this will be the rain amount distribution. 
    #### This step is probably the limiting factor and might be able to be made more efficient - I had a clever trick in matlab, but it doesn't work in python
    testpamtmap=np.empty(thisppdfmap.shape)
    for ibin in range(len(bins)-1):
        testpamtmap[:,:,ibin]=(pdata*(ibin==binno)).sum(axis=2)
    thispamtmap=testpamtmap/ndmat
    return thisppdfmap,thispamtmap

