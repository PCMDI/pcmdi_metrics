import cdms2 as cdms
import string
import ESMP

##### TARGET GRID FOR METRICS CALCULATION
def get_target_grid(tg,datapath):
 if tg == '2.5x2.5':
  ftarget = datapath + 'obs/atm/mo/tas/ERA40/ac/tas_ERA40_000001-000012_ac.nc'
  ft = cdms.open(ftarget)
  dt = ft('tas')
  obsg = dt.getGrid()
  ft.close()
  return obsg 

#### GET INHOUSE DATA THAT HAS BEEN TRANSFORMED/INTERPOLATED

def get_our_model_clim(experiment,var):

# HARDWIRED EXAMPLE ONLY !!!!!!!
  pd = '/work/gleckler1/processed_data/cmip5clims/' + var + '/' + 'cmip5.HadCM3.historical.r1i1p1.mo.atm.Amon.' + var + '.ver-1.1980-1999.AC.nc'
  f = cdms.open(pd)
  dm = f(var + '_ac')
  f.close()
  return dm 

########################################################################
#### GET OBSERVATIONAL DATA 

def get_obs(var,ref,outdir):

  obs_dic = {'rlut':{'default':'CERES','alternate':'ERBE'},
           'rsut':{'default':'CERES','alternate':'ERBE'},
           'rlutcs':{'default':'CERES','alternate':'ERBE'},
           'rsutcs':{'default':'CERES','alternate':'ERBE'},
           'rsutcre':{'default':'CERES','alternate':'ERBE'},
           'rlutcre':{'default':'CERES','alternate':'ERBE'},
           'pr':{'default':'GPCP','alternate':'CMAP'},
           'prw':{'default':'RSS'},
           'tas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'ua':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'va':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'uas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'vas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'ta':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'zg':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
            }

  datapath = outdir + 'obs/atm/mo/' 
  outdir = datapath + var + '/' + obs_dic[var][ref] + '/ac/' + var + '_' + obs_dic[var][ref] + '_000001-000012_ac.nc' 
  print outdir
  f = cdms.open(outdir)
  do = f(var)
  f.close()
  print var,' ---------- ', outdir
  return do
###################################################


## SCRATCH FOR NOW
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

