import cdms2 as cdms
import string
import ESMP

##### TARGET GRID FOR METRICS CALCULATION
def get_target_grid(tg):
 if tg == '2.5x2.5':
  ftarget = '../../data/obs/atm/mo/tas/ERA40/ac/tas_ERA40_000001-000012_ac.nc'
  ft = cdms.open(ftarget)
  dt = ft('tas')
  obsg = dt.getGrid()
  ft.close()
  return obsg 

#### GET INHOUSE DATA THAT HAS BEEN TRANSFORMED/INTERPOLATED

def get_our_model_clim(experiment,var,targetgrid):
  pathin = '../../data/inhouse_model_clims/' + experiment + '/atm/mo/ac/'
  file = 'cmip5_' + var + '_' + targetGrid + '.nc' 
  pathfile = pathin + file
  f = cdms.open(pathfile)
  d = f(var)
  f.close()
  return d 

#### GET OBSERVATIONAL DATA 

def get_obs(var,ref,outdir,targetGrid):

  obs_dic = {'rlut':{'ref1':'CERES','ref2':'ERBE'},
           'rsut':{'ref1':'CERES','ref2':'ERBE'},
           'rlutcs':{'ref1':'CERES','ref2':'ERBE'},
           'rsutcs':{'ref1':'CERES','ref2':'ERBE'},
           'rsutcre':{'ref1':'CERES','ref2':'ERBE'},
           'rlutcre':{'ref1':'CERES','ref2':'ERBE'},
           'pr':{'ref1':'GPCP','ref2':'CMAP'},
           'prw':{'ref1':'RSS'},
           'tas':{'ref1':'ERAINT','ref3':'JRA25','ref2':'rnl_ncep'},
           'ua':{'ref1':'ERAINT','ref3':'JRA25','ref2':'rnl_ncep'},
           'va':{'ref1':'ERAINT','ref3':'JRA25','ref2':'rnl_ncep'},
           'uas':{'ref1':'ERAINT','ref3':'JRA25','ref2':'rnl_ncep'},
           'vas':{'ref1':'ERAINT','ref3':'JRA25','ref2':'rnl_ncep'},
           'ta':{'ref1':'ERAINT','ref3':'JRA25','ref2':'rnl_ncep'},
           'zg':{'ref1':'ERAINT','ref3':'JRA25','ref2':'rnl_ncep'},
            }

  outdir = '/work/gleckler1/processed_data/metrics_package/obs/atm/mo/' + var + '/' + obs_dic[var][ref] + '/ac/' + var + '_' + obs_dic[var][ref] + '_000001-000012_ac.nc' 
  f = cdms.open(outdir)
  d = f(var)
  f.close()
  print '---------- ', outdir

### REGRID OBS
  obsg = get_target_grid(targetGrid)
  dnew = d.regrid(obsg,regridTool='regrid2')
  dnew.id = var

  return dnew

variable_list = [
['long_name','output_variable_name','input_variable_name','units'],
['Precipitation','pr','pr','kg m-2 s-1'],
['Water Vapor Path','prw','prw','kg m-3'],
['Surface Upwelling Longwave Radiation','rlus','rlus','W m-2'],
['TOA Outgoing Longwave Radiation','rlut','rlut','W m-2'],
['Surface Downwelling Shortwave Radiation','rsds','rsds','W m-2'],
['Surface Upwelling Shortwave Radiation','rsus','rsus','W m-2'],
['Net Downward Flux at Top of Model','rtmt','rtmt','W m-2'],
['Sea Surface Salinity','sos','sos','1e-3'],
['Air Temperature','ta','ta','K'],
['Surface Air Temperature','tas','tas','K'],
['Sea Surface Temperature','tos','tos','K'],
['Eastward Wind','ua','ua','m s-1'],
['Northward Wind','ua','ua','m s-1'],
['Geopotential Height','zg','zg','m'],
['Sea Surface Height Above Geoid','zos','zos','m'],
] ;

