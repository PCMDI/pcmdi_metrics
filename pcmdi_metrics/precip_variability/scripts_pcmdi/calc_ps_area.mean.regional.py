import xcdat as xc
import numpy as np
import pickle
import glob
import os
import sys
import datetime


#--------------------
# User settings here
#--------------------
# List of domain names
# e.g. ['CONUS']
domains=[]
# Which ensembles are included
# e.g. ['cmip6','obs']
mips=[]
# Input directories. Replace model, realization,
# and other variables with wildcard as needed
# Replace domain name references with '%(domain)'
model_root = ''
obs_root = ''
# Output directory (not including version)
outdir = ''

#-----------------------
# The rest of the script
#-----------------------
ver = datetime.datetime.now().strftime("v%Y%m%d")

frcs=['forced','unforced']

vars=['power','rednoise','sig95']

psdm={}

for ifc, frc in enumerate(frcs):
    psdm[frc]={}
    for dom in domains:
        for im, mip in enumerate(mips):
            if mip not in psdm[frc]:
                psdm[frc][mip]={}
            dir = '/'
            if mip=="cmip6":
                root=model_root.replace('%(domain)',dom)
            elif mip=="obs":
                root=obs_root.replace('%(domain)',dom)
            print(root)
            if(frc=='forced'):
                file_list = sorted(set(glob.glob(os.path.join(root,'PS*')))-set(glob.glob(os.path.join(root,'PS*_unforced.nc'))) - set(glob.glob(os.path.join(root,'PS*.json'))))
            elif(frc=='unforced'):
                file_list = sorted(set(glob.glob(os.path.join(root,'PS*_unforced.nc'))))

            data=[]
            for file in file_list:
                print("File (first loop): ",file)
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
            print("DATA: ",data)

            for id, dat in enumerate(data):
                #freqs = f[id]['freqs']
                print("File (second loop): ",file_list[id])
                frds = xc.open_dataset(file_list[id])
                if dat not in psdm[frc][mip]:
                    psdm[frc][mip][dat]={}
                if 'freqs' not in psdm[frc][mip][dat]:
                    psdm[frc][mip][dat]['freqs']=list(frds["freqs"])
                for iv, var in enumerate(vars):
                    print(frc,mip,dat,var)
                    if var not in psdm[frc][mip][dat]:
                        psdm[frc][mip][dat][var]={}
                    am = frds.spatial.average(var,axis=["X","Y"],weights="generate")[var]
                    psdm[frc][mip][dat][var][dom]=list(am.data)
                frds.close()

res = os.path.basename(file_list[0]).split("_")[2].split(".")[1]
hr = os.path.basename(file_list[0]).split("_")[1].split(".")[1]

outdir = os.path.join(outdir,ver) # add version to outdir
if not(os.path.isdir(outdir)):
    os.makedirs(outdir)

outfile=open(os.path.join(outdir,'PS_pr.{0}_regrid.{1}_area.mean.pkl'.format(hr,res)),'wb')
pickle.dump(psdm,outfile)
outfile.close()



