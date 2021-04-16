import cdutil
import numpy as np
import pickle
import json
import copy
import os

def prdday_to_frq3hridx(prdday,frequency):
    frq3hr=1./(float(prdday)*8.)
    idx = (np.abs(frequency-frq3hr)).argmin()
    return int(idx)

ver='v20210123'

frqs_forced=['semi-diurnal','diurnal','semi-annual','annual']
frqs_unforced=['sub-daily','synoptic','sub-seasonal','seasonal-annual','interannual']

indir = '/work/ahn6/pr/variability_across_timescales/power_spectrum/'+ver+'/data/'
infile = open(indir+'PS_pr.3hr_regrid.180x90_area.mean_obs.cmip5.cmip6.pkl', 'rb')
psdm = pickle.load(infile)

psdmfm=copy.deepcopy(psdm)
for frc in psdm.keys():
    if (frc=='forced'):
        frqs=frqs_forced
    elif (frc=='unforced'):    
        frqs=frqs_unforced

    for mip in psdm[frc].keys():

        for dat in psdm[frc][mip].keys():
            frequency=np.array(psdm[frc][mip][dat]['freqs'])
            del psdm[frc][mip][dat]['freqs']
            del psdmfm[frc][mip][dat]['freqs']

            for var in psdm[frc][mip][dat].keys():

                for idm, dom in enumerate(psdm[frc][mip][dat][var].keys()):
                    am=np.array(psdm[frc][mip][dat][var][dom])
                    del psdmfm[frc][mip][dat][var][dom]
                    psdmfm[frc][mip][dat][var][dom] = {}

                    for frq in frqs:
                        if (frq=='semi-diurnal'): # pr=0.5day
                            idx=prdday_to_frq3hridx(0.5,frequency)
                            amfm = am[idx]
                        elif (frq=='diurnal'): # pr=1day
                            idx=prdday_to_frq3hridx(1,frequency)
                            amfm = am[idx]
                        elif (frq=='semi-annual'): # 180day=<pr=<183day
                            idx2=prdday_to_frq3hridx(180,frequency)
                            idx1=prdday_to_frq3hridx(183,frequency)
                            amfm = cdutil.averager(am[idx1:idx2+1], weights='unweighted')
                        elif (frq=='annual'): # 360day=<pr=<366day
                            idx2=prdday_to_frq3hridx(360,frequency)
                            idx1=prdday_to_frq3hridx(366,frequency)
                            amfm = cdutil.averager(am[idx1:idx2+1], weights='unweighted')
                        elif (frq=='sub-daily'): # pr<1day
                            idx1=prdday_to_frq3hridx(1,frequency)
                            amfm = cdutil.averager(am[idx1+1:], weights='unweighted')
                        elif (frq=='synoptic'): # 1day=<pr<20day
                            idx2=prdday_to_frq3hridx(1,frequency)
                            idx1=prdday_to_frq3hridx(20,frequency)
                            amfm = cdutil.averager(am[idx1+1:idx2+1], weights='unweighted')
                        elif (frq=='sub-seasonal'): # 20day=<pr<90day
                            idx2=prdday_to_frq3hridx(20,frequency)
                            idx1=prdday_to_frq3hridx(90,frequency)
                            amfm = cdutil.averager(am[idx1+1:idx2+1], weights='unweighted')
                        elif (frq=='seasonal-annual'): # 90day=<pr<365day
                            idx2=prdday_to_frq3hridx(90,frequency)
                            idx1=prdday_to_frq3hridx(365,frequency)
                            amfm = cdutil.averager(am[idx1+1:idx2+1], weights='unweighted')
                        elif (frq=='interannual'): # 365day=<pr
                            idx2=prdday_to_frq3hridx(365,frequency)
                            amfm = cdutil.averager(am[:idx2+1], weights='unweighted')

                        psdmfm[frc][mip][dat][var][dom][frq] = amfm.tolist()


outdir='/work/ahn6/pr/variability_across_timescales/power_spectrum/'+ver+'/data'
if not(os.path.isdir(outdir)):
    os.makedirs(outdir)

outfile=open(outdir+'/PS_pr.3hr_regrid.180x90_area.freq.mean_obs.cmip5.cmip6.pkl','wb')
pickle.dump(psdmfm, outfile)
outfile.close()

outfile = open(outdir+'/PS_pr.3hr_regrid.180x90_area.freq.mean_obs.cmip5.cmip6.json','w')
json.dump(psdmfm, outfile, sort_keys=True, indent=4, separators=(',', ': '))
outfile.close()


