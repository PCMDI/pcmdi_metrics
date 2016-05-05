import sys, os
import string
#import durolib    ## P. Durack functions for determing 'latest' xml files
import subprocess
import cdms2 as cdms
import cdutil
import genutil
import time
import json

libfiles = ['durolib.py',
            'get_pcmdi_data.py',
            'PMP_rectangular_domains.py',
            'monthly_variability_statistics.py',
            'slice_tstep.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

mip = 'cmip5'
exp = 'piControl'
mod = 'IPSL-CM5B-LR'
fq = 'mo'
realm = 'atm'
var = 'ts'
run = 'r1i1p1'

#test = True
test = False

if test:
  mods = ['IPSL-CM5B-LR']  # Test just one model
  fdbs = ['AtmBjerk'] # Test just one region
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  #fdbs = ['AtmBjk','SfcFlx','SrtWav','LthFlx']
  fdbs = ['AtmBjk','SrtWav','LthFlx']

enso_stats_dic = {}  # Dictionary to be output to JSON file

for mod in mods:
  print ' ----- ', mod,' ---------------------'
  try:
    enso_stats_dic[mod] = {}   # create a dictionary within main dictionary
    enso_stats_dic[mod]['feedback'] = {}   # create an additional level of dictionary

    # x-axis of slope, common for all type of feedback
    xvar='ts'
    xregion = 'Nino3'
    reg_timeseries_x_area_avg_anom = get_axis_base_dataset(xvar,xregion)

    # y-axis of slope for each feedback
    for fdb in fdbs:  ### Too messy... there should be better way... working on it..

      if fdb == 'AtmBjk': # Atmospheric Bjerknes Feedback
        yvar = 'tauu'
        yregion = 'Nino4'
      elif fdb == 'SfcFlx': # Surface Fluxes Feedback
        yvar = 'hfls'
        yvar2 = 'hfss'
        yregion = 'Nino3'
      elif fdb == 'SrtWav': # Shortwave Feedback
        yvar='rsds'
        yregion = 'Nino3'
      elif fdb == 'LthFlx': # Latent Heat Fluexs Feedback
        yvar = 'hfls'
        yregion = 'Nino3'
      else:
        sys.exit(fdb+" is not defined")

      reg_timeseries_y_area_avg_anom = get_axis_base_dataset(yvar,yregion)

      if fdb == 'SfcFlx':
        reg_timeseries_y2_area_avg_anom = get_axis_base_dataset(yvar2,yregion)
        reg_timeseries_y_area_avg_anom = sum(reg_timeseries_y_area_avg_anom,reg_timeseries_y2_area_avg_anom)

      # Simple quality control
      if len(reg_timeseries_x_area_avg_anom) == len(reg_timeseries_y_area_avg_anom):
        ntstep = len(reg_timeseries_x_area_avg_anom)
      else:
        print xvar+" and "+yvar+" tstep not match"
        break

      slope = get_slope_linear_regression(reg_timeseries_y_area_avg_anom,reg_timeseries_x_area_avg_anom)
      print mod, fdb, 'slope =', slope
      enso_stats_dic[mod]['feedback'][fdb] = slope

    print 'reg_time =', ntstep
    enso_stats_dic[mod]['reg_time'] = ntstep

  except:
    print 'failed for model ', mod

# Write dictionary to json file
json_filename = 'AtmFeedback_' + mip + '_' + exp + '_' + run + '_' + fq + '_' +realm + '_' + var
json.dump(enso_stats_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

print 'all done for', var
