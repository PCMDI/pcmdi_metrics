#!/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 11:39:31 2014

File was created to generate land-sea masks for various reanalysis datasets, obtained from a range
of different sources both land-sea masks and land-only variables (as available)

Paul J. Durack 20th October 2014

PJD 20 Oct 2014     - Processed ERAInterim and JRA25 masks
PJD 21 Oct 2014     - Processed ERA40 mask

@author: durack1
"""
import os
from durolib import globalAttWrite
import cdms2 as cdm
import numpy as np
import MV2 as mv

# Set netcdf file criterion - turned on from default 0s
cdm.setCompressionWarnings(0) ; # Suppress warnings
cdm.setNetcdfShuffleFlag(0)
cdm.setNetcdfDeflateFlag(1)
cdm.setNetcdfDeflateLevelFlag(9)
cdm.setAutoBounds(1)

# JRA25
infile = '/work/durack1/Shared/obs_data/pcmdi_metrics/197901/anl_land25.ctl'
f_h = cdm.open(infile)
soilwhbl = f_h('soilwhbl')[0,0,...]
landMask = soilwhbl.mask
lat = soilwhbl.getLatitude()
lon = soilwhbl.getLongitude()

# Convert to percentage
landMask = landMask*100 ; # Convert to boolean fraction

# Rename
landMask = cdm.createVariable(landMask,id='sftlf',axes=soilwhbl.getAxisList(),typecode='float32')
landMask.original_name = "soilwhbl" ;
landMask.associated_files = "baseURL: http://rda.ucar.edu/datasets/ds625.0" ;
landMask.long_name = "Land Area Fraction" ;
landMask.standard_name = "land_area_fraction" ;
landMask.units = "%" ;
landMask.setMissing(1.e20)

# Regrid to current obs data
gridFile = '/clim_obs/obs/atm/mo/tas/JRA25/ac/tas_JRA25_000001-000012_ac.nc'
f_g = cdm.open(gridFile)
grid = f_g('tas').getGrid()
landMask = landMask.regrid(grid,regridTool='ESMF',regridMethod='linear')
f_g.close()
landMask.id = 'sftlf' ; # Rename

# Deal with interpolated values
landMask[mv.greater(landMask,75)] = 100 ; # Fix weird ocean values
landMask[mv.less(landMask,75)] = 0 ; # Fix continental halos
landMask[mv.less(landMask,0)] = 0 ; # Fix negative values

# Invert land=100, ocean=0
landMask[mv.equal(landMask,0)] = 50 ; # Convert ocean
landMask[mv.equal(landMask,100)] = 0 ; # Convert ocean
landMask[mv.equal(landMask,50)] = 100 ; # Convert ocean

# Create outfile and write
outFile = 'sftlf_pcmdi-metrics_fx_NCAR-JRA25_197901-201401.nc'
# Write variables to file
if os.path.isfile(outFile):
    os.remove(outFile)
fOut = cdm.open(outFile,'w')
globalAttWrite(fOut,options=None) ; # Use function to write standard global atts
fOut.pcmdi_metrics_version = '0.1-alpha'
fOut.pcmdi_metrics_comment = 'This climatology was prepared by PCMDI for the metrics package and is intended for research purposes only'
fOut.write(landMask.astype('float32'))
fOut.close()
f_h.close()

# ERAInterim
infile = '/work/durack1/Shared/obs_data/pcmdi_metrics/141019_ERAInt-lsm_netcdf-atls03-20141019213028-36373-3245.nc'
f_h = cdm.open(infile)
lsm = f_h('lsm')[0,...]
landMask = np.array(lsm)
lat = lsm.getLatitude()
lon = lsm.getLongitude()

# Convert to percentage
landMask = landMask*100 ; # Convert to boolean fraction

# Flip latitude
landMask = np.flipud(landMask)
newAxes = lsm.getAxisList()
newLat = cdm.createAxis(np.flipud(lat.getValue()),id=lat.id)
newLat.designateLatitude
for count,att in enumerate(lat.attributes.keys()):
    setattr(newLat,att,lat.attributes.get(att))
newAxes[0] = newLat

# Rename
landMask = cdm.createVariable(landMask,id='sftlf',axes=newAxes,typecode='float32')
landMask.original_name = "lsm" ;
landMask.associated_files = "baseURL: http://apps.ecmwf.int/datasets/data/interim_full_invariant/" ;
landMask.long_name = "Land Area Fraction" ;
landMask.standard_name = "land_area_fraction" ;
landMask.units = "%" ;
landMask.setMissing(1.e20)

# Create outfile and write
outFile = 'sftlf_pcmdi-metrics_fx_ECMWF-ERAInterim_197901-201407.nc'
# Write variables to file
if os.path.isfile(outFile):
    os.remove(outFile)
fOut = cdm.open(outFile,'w')
globalAttWrite(fOut,options=None) ; # Use function to write standard global atts
fOut.pcmdi_metrics_version = '0.1-alpha'
fOut.pcmdi_metrics_comment = 'This climatology was prepared by PCMDI for the metrics package and is intended for research purposes only'
fOut.write(landMask.astype('float32'))
fOut.close()
f_h.close()


# ERA40
infile = '/work/durack1/Shared/obs_data/pcmdi_metrics/141021_ERA40_swvl1-netcdf-atls03-20141021145335-36433-5059.nc'
f_h = cdm.open(infile)
swvl1 = f_h('swvl1')[0,...]
landMask = np.array(swvl1)
lat = swvl1.getLatitude()
lon = swvl1.getLongitude()

# Deal with land values
landMask[np.greater(landMask,1e-15)] = 100

# Flip latitude
landMask = np.flipud(landMask)
newAxes = swvl1.getAxisList()
newLat = cdm.createAxis(np.flipud(lat.getValue()),id=lat.id)
newLat.designateLatitude
for count,att in enumerate(lat.attributes.keys()):
    setattr(newLat,att,lat.attributes.get(att))
newAxes[0] = newLat

# Rename
landMask = cdm.createVariable(landMask,id='sftlf',axes=newAxes,typecode='float32')
landMask.original_name = "lsm" ;
landMask.associated_files = "baseURL: http://apps.ecmwf.int/datasets/data/era40_daily/" ;
landMask.long_name = "Land Area Fraction" ;
landMask.standard_name = "land_area_fraction" ;
landMask.units = "%" ;
landMask.setMissing(1.e20)

# Create outfile and write
outFile = 'sftlf_pcmdi-metrics_fx_ECMWF-ERA40_195709-200208.nc'
# Write variables to file
if os.path.isfile(outFile):
    os.remove(outFile)
fOut = cdm.open(outFile,'w')
globalAttWrite(fOut,options=None) ; # Use function to write standard global atts
fOut.pcmdi_metrics_version = '0.1-alpha'
fOut.pcmdi_metrics_comment = 'This climatology was prepared by PCMDI for the metrics package and is intended for research purposes only'
fOut.write(landMask.astype('float32'))
fOut.close()
f_h.close()
