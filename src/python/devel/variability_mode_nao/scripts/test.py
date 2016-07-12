import sys, os
import string
import subprocess
import cdms2 as cdms
import cdutil
import genutil
import time
import json
from eofs.cdms import Eof

libfiles = ['durolib.py',
            'get_pcmdi_data.py']
#libfiles = ['get_pcmdi_data.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

mip = 'cmip5'
exp = 'piControl'
mod = 'ACCESS1-0'
fq = 'mo'
realm = 'atm'
var = 'psl'
run = 'r1i1p1'

test = True
#test = False

if test:
  mods = ['ACCESS1-0']  # Test just one model
  seasons = ['DJF']
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  seasons = ['DJF','MAM','JJA','SON']

for mod in mods:
  #mod_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,var,run)
  mod_path = '/work/cmip5/piControl/atm/mo/psl/cmip5.ACCESS1-0.piControl.r1i1p1.mo.atm.Amon.psl.ver-1.latestX.xml'

  print mod_path

  f = cdms.open(mod_path)

  if test:
    mod_timeseries = f(var,longitude=(-180,180),time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
  else:
    mod_timeseries = f(var,longitude=(-180,180))

  ntstep = len(mod_timeseries)
  print ntstep

  for season in seasons:
    mod_timeseries_season = getattr(cdutil,season)(mod_timeseries)

    # EOF
    #solver = Eof(mod_timeseries_season, weights='coslat')
    #solver = Eof(mod_timeseries_season(latitude=(20,80),longitude=(-90,40)), weights='coslat')
    solver = Eof(mod_timeseries_season(latitude=(0,90),longitude=(-180,180)), weights='coslat')

    adj_sign = 1.
    sign_reverse = False
    if sign_reverse == True:
      adj_sign = -1.

    eof1 = solver.eofsAsCovariance(neofs=1)*adj_sign
    #eof1 = solver.eofsAsCorrelation(neofs=1)*adj_sign
    pc1 = solver.pcs(npcs=1, pcscaling=1)*adj_sign
    var_frac1 = solver.varianceFraction()[0]

    fout = cdms.open('nao_eof1_'+mod+'_'+season+'.nc','w')
    fout.write(eof1)
    #fout.write(pc1)
    #fout.write(var_frac1)
    #fout.write(mod_timeseries_season)
    fout.close()

    import vcs
    y=vcs.init()
    y.setcolormap("blue_to_orange")
    y.plot(eof1)

    x=vcs.init()
    x.setcolormap("blue_to_orange")
    gm = vcs.createisofill()
    p = vcs.createprojection()
    ptype = int('-3')
    p.type = ptype
    gm.projection = p
    xtra = {}
    xtra["latitude"] = (90.0,0.0)
    eof1=eof1(**xtra)
    x.plot(eof1,gm)
