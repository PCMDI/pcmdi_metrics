import cdms2 as cdms
import MV2 as MV
import numpy as np
import pickle
import glob
import cdutil
import genutil
import os

ver='v20210123'

domains=['Total_50S50N' ,'Ocean_50S50N' ,'Land_50S50N',
         'Total_30N50N' ,'Ocean_30N50N' ,'Land_30N50N',
         'Total_30S30N' ,'Ocean_30S30N' ,'Land_30S30N',
         'Total_50S30S' ,'Ocean_50S30S' ,'Land_50S30S']

mips=['obs','cmip5','cmip6']

frcs=['forced','unforced']

vars=['power','rednoise','sig95']

psdm={}
for ifc, frc in enumerate(frcs):
    
    psdm[frc]={}
    for im, mip in enumerate(mips):
        dir = '/work/ahn6/pr/variability_across_timescales/power_spectrum/'+ver+'/data/'+mip+'/'
        if(frc=='forced'):
            file_list = sorted(set(glob.glob(dir+'PS*'))-set(glob.glob(dir+'PS*_unforced.nc')))
        elif(frc=='unforced'):
            file_list = sorted(set(glob.glob(dir+'PS*_unforced.nc')))
        
        f=[]
        data=[]
        for ifl in range(len(file_list)):
            f.append(cdms.open(file_list[ifl]))
            file=file_list[ifl]
            if(mip=='obs'):
                tmp = file.split('/')[-1].split('_')[3]
                model = tmp.split('.')[0]
                data.append(model)
            else:
                tmp = file.split('/')[-1].split('_')[3]
                model = tmp.split('.')[0]
                ens = tmp.split('.')[1]
                data.append(model+'.'+ens)
        print(mip, '# of data:', len(data))
        print(data)

        psdm[frc][mip]={}
        for id, dat in enumerate(data):
            freqs = f[id]['freqs']

            psdm[frc][mip][dat]={}
            psdm[frc][mip][dat]['freqs']=freqs[:].tolist()
            for iv, var in enumerate(vars):
                print(frc,mip,dat,var)
                d = f[id][var]
                mask = cdutil.generateLandSeaMask(d[0])
                d, mask2 = genutil.grower(d, mask)
                d_ocean = MV.masked_where(mask2==1., d)
                d_land  = MV.masked_where(mask2==0., d)

                psdm[frc][mip][dat][var]={}
                for idm, dom in enumerate(domains):

                    if 'Ocean' in dom:
                        dmask = d_ocean
                    elif 'Land' in dom:
                        dmask = d_land
                    else:
                        dmask = d

                    if '50S50N' in dom:
                        am = cdutil.averager(dmask(latitude=(-50,50)), axis='xy')
                    if '30N50N' in dom:
                        am = cdutil.averager(dmask(latitude=(30,50)), axis='xy')
                    if '30S30N' in dom:
                        am = cdutil.averager(dmask(latitude=(-30,30)), axis='xy')
                    if '50S30S' in dom:
                        am = cdutil.averager(dmask(latitude=(-50,-30)), axis='xy')

                    psdm[frc][mip][dat][var][dom]=am.tolist()

outdir='/work/ahn6/pr/variability_across_timescales/power_spectrum/'+ver+'/data'
if not(os.path.isdir(outdir)):
    os.makedirs(outdir)
outfile=open(outdir+'/PS_pr.3hr_regrid.180x90_area.mean_obs.cmip5.cmip6.pkl','wb')
pickle.dump(psdm,outfile)
outfile.close()


