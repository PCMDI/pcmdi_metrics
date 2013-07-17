import cdms2 as cdms
import string, os
import ESMP

#### TARGET GRID FOR METRICS CALCULATION
def get_target_grid(tg,datapath):
 if tg == '2.5x2.5':
  ftarget = datapath + 'obs/atm/mo/tas/ERA40/ac/tas_ERA40_000001-000012_ac.nc'
  ft = cdms.open(ftarget)
  dt = ft('tas')
  obsg = dt.getGrid()
  ft.close()
  return obsg 

#### MAKE DIRECTORY
def mkdir_fcn(path):
 try:
     os.mkdir(path)
 except:
     pass
 return

#### GET INHOUSE DATA THAT HAS BEEN TRANSFORMED/INTERPOLATED

def get_our_model_clim(data_location,var):

  pd = data_location
# if var in ['tos','sos','zos']: pd = string.replace(pd,'atm.Amon','ocn.Omon')
  f = cdms.open(pd)
  try:
   dm = f(var + '_ac')
  except:
   dm = f(var)

  f.close()
  return dm 

#### GET CMIP5 DATA

def get_cmip5_model_clim(data_location,model_version, var):

  lst = os.popen('ls ' + data_location + '*' + model_version + '*' + var + '.*.nc').readlines()

  pd = lst[0][:-1]   #data_location
# if var in ['tos','sos','zos']: pd = string.replace(pd,'atm.Amon','ocn.Omon')
  f = cdms.open(pd)
  try:
   dm = f(var + '_ac')
  except:
   dm = f(var)
  f.close()
  print pd
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
           'tos':{'default':'HadISST'},
           'zos':{'default':'CNES_AVISO'},
           'sos':{'default':'WOA09'},
            }

  datapath = outdir + 'obs/atm/mo/' 
  if var in ['tos','sos','zos']: datapath = string.replace(datapath,'atm','ocn')
 
# outdir = datapath + var + '/' + obs_dic[var][ref] + '/ac/' + var + '_' + obs_dic[var][ref] + '_000001-000012_ac.nc' 
# if var == 'zos': 
#   outdir = datapath + var + '/' + obs_dic[var][ref] + '/ac/' + 'zos_CNES_AVISO_L4_199201-200512_ac.nc' 
# if var == 'tos':
#   outdir = datapath + var + '/' + obs_dic[var][ref] + '/ac/' + 'tos_HadISST_198001-200512_ac.nc'

  outdir = datapath + var + '/' + obs_dic[var][ref] + '/ac/'
  lst = os.listdir(outdir)
  fc = outdir + lst[0] 

# print outdir
  f = cdms.open(fc)
  do = f(var)
  f.close()
# print var,' ---------- ', outdir
  return do
###################################################

def output_model_clims(dm,var,Tdir,F, model_version, targetGrid):
 pathout = Tdir() 
 try:
  os.mkdir(pathout)
 except:
  pass

 F.variable = var
 F.model_version = model_version
 nm = F()
 nm = string.replace(nm,'.nc','.' + targetGrid + '.nc')

 dm.id = var
 g = cdms.open(pathout + '/' + nm,'w+') 
 g.write(dm)
 g.close()

def model_output_structure(dir_template, file_template, model_version, variable):
 dir_template = "%(root_modeling_group_clim_directory)/%(test_case)/" 
 ### CONSTRUCT PATH
 D=genutil.StringConstructor(dir_template)
 D.root_modeling_group_clim_directory = mod_data_path
 D.test_case = test_case
 data_location = D()

 ### CONSTRUCT FILENAME 
 F = genutil.StringConstructor(file_template) 
 F.model_version = model_version
 F.table_realm = 'atm.Amon'
 if variable in ['tos','sos','zos']:  F.table_realm = 'ocn.Omon'
 F.variable = variable
 F.ext='nc'
 F.period = '1980-2005'
 filename = F()

 return data_location,filename

def output_interpolated_model_data(dm, var, targetGrid,regrid_method,model_output_location):

 model_output_location = string.replace(model_output_location,'.nc','.' + regrid_method + '.' + targetGrid + '.nc') 

 g = cdms.open(model_output_location,'w+')
 dm.id = var
 g.write(dm)
 g.close() 


