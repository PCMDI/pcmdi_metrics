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

region = 'NH' # Northern Hemisphere
region = 'NA' # Northern Atlantic

if test:
  #models = ['ACCESS1-0']  # Test just one model
  models = ['ACCESS1-3']  # Test just one model
  seasons = ['DJF']
else:
  models = get_all_mip_models(mip,exp,fq,realm,var)
  seasons = ['DJF','MAM','JJA','SON']

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

  if region == 'NH':
    lat1 = 0
    lat1 = 20
    lat2 = 90
    lon1 = -180
    lon2 = 180
  elif region == 'NA':
    lat1 = 20
    lat2 = 80
    lon1 = -90
    lon2 = 40
  model_timeseries = f(var,latitude=(lat1,lat2),longitude=(lon1,lon2),time=(start_time,end_time))/100. # Pa to hPa
  cdutil.setTimeBoundsMonthly(model_timeseries)

  for season in seasons:
    model_timeseries_season = getattr(cdutil,season)(model_timeseries)

    # EOF
    solver = Eof(model_timeseries_season, weights='coslat')
    #solver = Eof(model_timeseries_season(latitude=(0,90),longitude=(-180,180)), weights='coslat')
    #solver = Eof(model_timeseries_season(latitude=(lat1,lat2),longitude=(lon1,lon2)), weights='coslat')

    eof1 = solver.eofsAsCovariance(neofs=1)
    pc1 = solver.pcs(npcs=1, pcscaling=1)
    frac1 = round(solver.varianceFraction()[0]*100.,1)

    # Arbitrary control, attempt to make all plots have the same sign -- 
    if float(eof1[0][-1][-1]) >= 0:
      eof1 = eof1*-1.
      pc1 = pc1*-1.

    ax = model_timeseries_season.getAxis(0)
    if ax.isTime():
      time = cdms.createAxis(range(1))
      time.id = ax.id
      time.units = ax.units
      eof1.setAxis(0,time)

    fout = cdms.open('nao_slp_eof1_'+season+'_'+model+'_'+str(syear)+'-'+str(eyear)+'_'+region+'.nc','w')
    fout.write(eof1)
    #fout.write(pc1)
    #fout.write(var_frac1)
    #fout.write(model_timeseries_season)
    fout.close()

    # Below is just for testing....
    #fout_test = cdms.open('test.nc','w')
    #fout_test.write(model_timeseries_season)
    #fout_test.close()

    #=================================================
    # PART 2 : GRAPHIC (plotting)
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
    if region == 'NH':
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
    plot_title.string = str.upper(model)+'\n'+str(syear)+'-'+str(eyear)+', '+str(frac1)+'%'
    canvas.plot(plot_title)

    #-------------------------------------------------
    # Drop output as image file (--- vector image?)
    #- - - - - - - - - - - - - - - - - - - - - - - - - 
    canvas.png('nao_slp_eof1_'+season+'_'+model+'_'+str(syear)+'-'+str(eyear)+'_'+region+'.png')

    if not test:
      canvas.close()
