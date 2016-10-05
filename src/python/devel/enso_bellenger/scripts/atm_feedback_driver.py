import sys, os
import shutil
import cdms2 as cdms
import json

libfiles = ['durolib.py',
            'get_pcmdi_data.py',
            'monthly_variability_statistics.py',
            'slice_tstep.py']

libfiles_share = ['default_regions.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

for lib in libfiles_share:
  execfile(os.path.join('../../../../../share/',lib))

##################################################
# Pre-defined options
#=================================================
mip = 'cmip5'
exp = 'piControl'
mod = 'IPSL-CM5B-LR'
fq = 'mo'
realm = 'atm'
var = 'ts'
run = 'r1i1p1'

out_dir = './result'
if not os.path.exists(out_dir): os.makedirs(out_dir)

#=================================================
# Additional options
#=================================================
debug = True
#debug = False

if debug:
  mods = ['IPSL-CM5B-LR']  # Test just one model
  fdbs = ['AtmBjk'] # Test just one region
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  fdbs = ['AtmBjk','SfcFlx','SrtWav','LthFlx']

#=================================================
# Declare dictionary for .json record 
#-------------------------------------------------
# Prepare dictionary frame
enso_stat_dic = {}  # Dictionary to be output to JSON file

json_filename = 'AtmFeedback_' + mip + '_' + exp + '_' + run + '_' + fq + '_' +realm + '_' + var

json_file = out_dir + '/' + json_filename + '.json'
json_file_org = out_dir + '/' + json_filename + '_org.json'

# Keep previous version of json file against overwrite ---
if os.path.isfile(json_file):
  shutil.copyfile(json_file, json_file_org)

update_json = True

if update_json == True and os.path.isfile(json_file):
  fj = open(json_file)
  enso_stat_dic = json.loads(fj.read())
  fj.close()

if 'REF' not in enso_stat_dic.keys():
  enso_stat_dic['REF']={}
if 'RESULTS' not in enso_stat_dic.keys():
  enso_stat_dic['RESULTS']={}

#=================================================
# Models 
#-------------------------------------------------
for mod in mods:
  print ' ----- ', mod,' ---------------------'

  #try:
  if 1 == 1:

    if mod not in enso_stat_dic['RESULTS'].keys():
      enso_stat_dic['RESULTS'][mod] = {}
    if 'feedback' not in enso_stat_dic['RESULTS'][mod].keys():
      enso_stat_dic['RESULTS'][mod]['feedback'] = {} 

    # x-axis of slope, common for all type of feedback
    xvar='ts'
    xregion = 'Nino3'
    xvar_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,xvar,run)
    reg_timeseries_x_area_avg_anom = get_axis_base_dataset(xvar, xregion, xvar_path)

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

      try:
        yvar_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,yvar,run)
        reg_timeseries_y_area_avg_anom = get_axis_base_dataset(yvar, yregion, yvar_path)

        if fdb == 'SfcFlx':
          yvar2_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,yvar2,run)
          reg_timeseries_y2_area_avg_anom = get_axis_base_dataset(yvar2, yregion, yvar2_path)
          reg_timeseries_y_area_avg_anom = sum(reg_timeseries_y_area_avg_anom,reg_timeseries_y2_area_avg_anom)

        # Simple quality control
        if len(reg_timeseries_x_area_avg_anom) == len(reg_timeseries_y_area_avg_anom):
          ntstep = len(reg_timeseries_x_area_avg_anom)
        else:
          print xvar+" and "+yvar+" tstep not match"
          break

        slope = get_slope_linear_regression(reg_timeseries_y_area_avg_anom,reg_timeseries_x_area_avg_anom)
        print mod, fdb, 'slope =', slope

        enso_stat_dic['RESULTS'][mod]['feedback'][fdb] = slope

      except:
        print mod, fdb, "cannot be calculated"

    if debug: print 'reg_time =', ntstep

    enso_stat_dic['RESULTS'][mod]['reg_time'] = ntstep

    # Write dictionary to json file
    json.dump(enso_stat_dic, open(json_file + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

  #except:
  #  print 'failed for model ', mod
  #  pass

print 'all done for', var
