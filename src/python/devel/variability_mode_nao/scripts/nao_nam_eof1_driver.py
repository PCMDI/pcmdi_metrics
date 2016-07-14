import sys, os
import string
import subprocess
import cdms2 as cdms
import cdutil
import cdtime
import genutil
import time
import json
from eofs.cdms import Eof
import vcs

#libfiles = ['durolib.py',
#            'get_pcmdi_data.py']
libfiles = ['get_pcmdi_data.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

mip = 'cmip5'
#exp = 'piControl'
exp = 'historical'
model = 'ACCESS1-0'
fq = 'mo'
realm = 'atm'
var = 'psl'
run = 'r1i1p1'

test = True
#test = False

mode = 'nam' # Northern Hemisphere
mode = 'nao' # Northern Atlantic

if test:
  #models = ['ACCESS1-0']  # Test just one model
  models = ['ACCESS1-3']  # Test just one model
  seasons = ['DJF']
else:
  models = get_all_mip_models(mip,exp,fq,realm,var)
  seasons = ['DJF','MAM','JJA','SON']

#=================================================
# First Tier loop
#-------------------------------------------------
for model in models:
  #model_path = get_latest_pcmdi_mip_data_path(mip,exp,model,fq,realm,var,run)
  #model_path = '/work/cmip5/piControl/atm/mo/psl/cmip5.ACCESS1-0.piControl.r1i1p1.mo.atm.Amon.psl.ver-1.latestX.xml'
  model_path = '/work/cmip5/historical/atm/mo/psl/cmip5.'+model+'.historical.r1i1p1.mo.atm.Amon.psl.ver-1.latestX.xml'
  #print model_path
  f = cdms.open(model_path)

  syear = 1900
  eyear = 2005

  start_time = cdtime.comptime(syear,1,1)
  end_time = cdtime.comptime(eyear,12,31) 

  if mode == 'nam':
    lat1 = 20
    lat2 = 90
    lon1 = -180
    lon2 = 180
  elif mode == 'nao':
    lat1 = 20
    lat2 = 80
    lon1 = -90
    lon2 = 40

  model_timeseries = f(var,latitude=(lat1,lat2),longitude=(lon1,lon2),time=(start_time,end_time))/100. # Pa to hPa
  cdutil.setTimeBoundsMonthly(model_timeseries)

  #=================================================
  # Second Tier loop
  #-------------------------------------------------
  for season in seasons:
    model_timeseries_season = getattr(cdutil,season)(model_timeseries)

    # EOF (take only first variance mode...) ---
    solver = Eof(model_timeseries_season, weights='coslat')
    eof = solver.eofsAsCovariance(neofs=1)
    pc = solver.pcs(npcs=1, pcscaling=1) # pcscaling=1: scaled to unit variance (divided by the square-root of their eigenvalue)
    frac = solver.varianceFraction()

    # Remove unnessasary dimensions (make sure only taking first variance mode) ---
    eof1 = eof(squeeze=1) # same as... eof1 = eof[0]
    pc1 = pc(squeeze=1)   #            pc1 = pc[:,0] 
    frac1 = cdms.createVariable(frac[0])

    # Arbitrary control, attempt to make all plots have the same sign ---
    if float(eof1[-1][-1]) >= 0:
      eof1 = eof1*-1.
      pc1 = pc1*-1.

    # Prepare dumping data to NetCDF file ---
    frac1.units = 'ratio'
    pc1.comment='Scaled time series for principal component of first variance mode'

    # Save in NetCDF output ---
    fout = cdms.open(mode+'_slp_eof1_'+season+'_'+model+'_'+str(syear)+'-'+str(eyear)+'_'+mode+'.nc','w')
    fout.write(eof1,id='eof1')
    fout.write(pc1,id='pc1')
    fout.write(frac1,id='frac1')
    fout.close()

    # Prepare OBS statistics (regrid will be needed) output writing to json file....


    #=================================================
    # GRAPHIC (plotting) PART
    #-------------------------------------------------
    # Create canvas
    canvas = vcs.init(geometry=(900,800))
    canvas.open()
    canvas.drawlogooff()
    template = canvas.createtemplate()

    # Turn off no-needed information -- prevent overlap
    template.blank(['title','mean','min','max','dataname','crdate','crtime',
                'units','zvalue','tvalue','xunits','yunits','xname','yname'])

    canvas.setcolormap('bl_to_darkred')
    iso = canvas.createisofill()
    iso.levels = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
    iso.ext_1 = 'y' # control colorbar edge (arrow extention on/off)
    iso.ext_2 = 'y' # control colorbar edge (arrow extention on/off)
    cols = vcs.getcolors(iso.levels)
    cols[6] = 139 # Adjsut to light red
    iso.fillareacolors = cols
    p = vcs.createprojection()
    if mode == 'NH':
      ptype = int('-3')
    else:
      ptype = 'lambert azimuthal'
    p.type = ptype
    iso.projection = p
    xtra = {}
    xtra['latitude'] = (90.0,0.0)
    eof1 = eof1(**xtra) # For NH projection 
    canvas.plot(eof1,iso,template)

    #-------------------------------------------------
    # Title
    #- - - - - - - - - - - - - - - - - - - - - - - - - 
    plot_title = vcs.createtext()
    plot_title.x = .5
    plot_title.y = .97
    plot_title.height = 23
    plot_title.halign = 'center'
    plot_title.valign = 'top'
    plot_title.color='black'
    frac1 = round(float(frac1*100.),1) # % with one floating number
    plot_title.string = str.upper(mode)+': '+str.upper(model)+'\n'+str(syear)+'-'+str(eyear)+' '+str.upper(season)+', '+str(frac1)+'%'
    canvas.plot(plot_title)

    #-------------------------------------------------
    # Drop output as image file (--- vector image?)
    #- - - - - - - - - - - - - - - - - - - - - - - - - 
    canvas.png(mode+'_slp_eof1_'+season+'_'+model+'_'+str(syear)+'-'+str(eyear)+'_'+mode+'.png')

    if not test:
      canvas.close()
