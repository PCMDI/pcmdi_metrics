import cdms2
import string, os
import ESMP

###################################### 
value = 0 
cdms2.setNetcdfShuffleFlag(value)
cdms2.setNetcdfDeflateFlag(value)
cdms2.setNetcdfDeflateLevelFlag(value)
######################################

### EXECUTE MODULE WITH VARIOUS FUNCTIONS
execfile('modules_and_functions/misc_module.py')
execfile('modules_and_functions/getOurModelData.py')

### OPTIONS FOR REGRIDDING: METHOD AND TARGET GRID
exp = 'cmip5'
rgridMeth = 'regrid2'
targetGrid = '4x5'
targetGrid = '2.5x2.5'

### OUTPUT DIRECTORY
outdir = '/work/metricspackage/130522/data/inhouse_model_clims/samplerun/atm/mo/ac/'
## SEE END OF THIS CODE FOR OUTPUT FILENAMES

### VARIABLES TO LOOP OVER (NAMES ASSUMED TO BE CONSISTENT WITH CMIP5)
vars = ['rlut','pr']

######################################

############# GET OBS TARGET GRID
obsg = get_target_grid(targetGrid)
############# 

#############

### LOOP THROUGH VARIABLES

for var in vars:

############# GET INHOUSE MODEL DATA 
   d = getOurModelData(exp,var)

############ REGRID DATA

   dnew = d.regrid(obsg,regridTool='regrid2')
   dnew.id = var

########### OUTPUT REGRIDDED DATA

   outPathName = outdir + exp + '_' + var + '_' + targetGrid + '.nc'

   g = cdms.open(outPathName,'w+')
   g.write(dnew)
   g.close()


