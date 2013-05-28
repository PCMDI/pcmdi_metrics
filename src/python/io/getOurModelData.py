import cdms2
import string  

##############################################################################
# PJG 20130522
# THIS FUNCTION IS EXPECTED TO BE MODIFIED BY USERS.  IT IS MEANT TO POINT TO 
# MODEL OUTPUT CLIMATOLOGIES THAT ARE USED BY THIS PACKAGE, IN PARTICULAR
# interpolate_new_model_to_metrics_grid.py
#
##### ASSUMPTIONS: 
#####  - THE MODEL DATA IS CF COMPLIANT AND STRUCTURED SIMILIAR TO CMIP5 DATA
#####  - MODEL OUTPUT IS A CLIMATOLOGY 
#####  - VARIABLE NAMES MATCH CMIP5 (BUT THIS CAN BE OVERRIDDEN)
 
##############################################################################


# EXAMPLE (@PCMDI)

def getOurModelData(exp,var):

 pathin = '/work/gleckler1/processed_data/' + exp + 'clims/'

 filename_tmp = 'cmip5.NorESM1-M.historical.r1i1p1.mo.atm.Amon.VARNAME.ver-1.1980-1999.AC.nc'

 filename_new = string.replace(filename_tmp,'VARNAME',var)

 f = cdms.open(pathin + var + '/' + filename_new)
 d = f(var + '_ac')
 f.close()

 return d






