import cdms2 as cdms
import string, os
import ESMP

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


