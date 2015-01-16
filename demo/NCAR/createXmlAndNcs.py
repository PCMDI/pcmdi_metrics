#!/glade/u/home/durack1/141104_metrics/PCMDI_METRICS/bin/python

"""
Created on Mon Nov 24 14:58:07 2014

Paul J. Durack 24th November 2014

This script scans netcdf files to create a composite xml spanning file
and then using this index file, writes netcdf files for each variable

PJD 24 Nov 2014     - Began script
PJD 24 Nov 2014     - Updated to include CNAR-CAM5* data
                    - Gary Strand provided variable remapping info: https://proxy.subversion.ucar.edu/CCP_Processing_Suite/CMOR2/Xwalks/
PJD 24 Nov 2014     - Limited input directories to 2, as running out of disk space with 0.25 deg simulations
PJD 24 Nov 2014     - Turned on netcdf4 file compression: 2 experiments 7.9Gb uncompressed -> 6.3Gb compressed
PJD 25 Nov 2014     - Added durolib/globalAttWrite
PJD 25 Nov 2014     - Added history and updated long_name for manipulated variables
                    - TODO:
                    - Need to confirm PR unit conversion, m/s -> kg m-2 s-1 requires additional inputs

@author: durack1
"""

# Python module imports
import os,shutil,subprocess,sys
import cdms2 as cdm
# Add durolib to path
sys.path.insert(1,'/glade/u/home/durack1')
from durolib import globalAttWrite


# Set cdms preferences - no compression, no shuffling, no complaining
cdm.setNetcdfDeflateFlag(1)
cdm.setNetcdfDeflateLevelFlag(9) ; # 1-9, min to max - Comes at heavy IO (read/write time cost)
cdm.setNetcdfShuffleFlag(0)
cdm.setCompressionWarnings(0) ; # Turn off nag messages
# Set bounds automagically
#cdm.setAutoBounds(1) ; # Use with caution

# Set build info once
buildDate = '141104'

# Create input variable lists 
uvcdatInstall = ''.join(['/glade/u/home/durack1/',buildDate,'_metrics/PCMDI_METRICS/bin/'])
data =  [
        ['atmos','NCAR-CAM5_1deg','f.e12.FAMIPC5.ne30_g16.amip.002_','/glade/p/cgd/amp/people/hannay/amwg/climo/f.e12.FAMIPC5.ne30_g16.amip.002/0.9x1.25/'],
        ['atmos','NCAR-CAM5_0p25deg','FAMIPC5_ne120_79to05_03_omp2_','/glade/p/cgd/amp/people/hannay/amwg/climo/FAMIPC5_ne120_79to05_03_omp2/0.23x0.31/'],
        ['atmos','NCAR-CAM5_0p25deg_interp_1deg','FAMIPC5_ne120_79to05_03_omp2_','/glade/p/cgd/amp/people/hannay/amwg/climo/FAMIPC5_ne120_79to05_03_omp2/0.9x1.25/']
]
inVarsAtm   = ['','QREFHT','','TMQ','PSL','FLDS','','FLUTC','FSDS','FSDSC','SOLIN','','TREFHT','TAUX','TAUY','','',''] ; # FLDSC
outVarsAtm  = ['hus','huss','pr','prw','psl','rlds','rlut','rlutcs','rsds','rsdscs','rsdt', \
               'ta','tas','tauu','tauv','ua','va','zg'] ; # uas,vas
varMatch    = ['hus','pr','rlut','ta','ua','va','zg'] ; # uas, vas
varCalc     = [[['Q','PS'],'Q interpolated to standard plevs'],[['PRECC','PRECL'],'PRECC + PRECL and unit conversion'],[['FSNTOA','FSNT','FLNT'],'FSNTOA-FSNT+FLNT'],[['T','PS'],'T interpolated to standard plevs'],[['U','PS'],'U interpolated to standard plevs'],[['V','PS'],'V interpolated to standard plevs'],[['Z3','PS'],'Z3 interpolated to standard plevs']]
inVarsOcn   = ['SALT','TEMP','SSH']
outVarsOcn  = ['sos','tos','zos']
'''
# Test lookup lists
for x,var in enumerate(outVarsAtm):
    if inVarsAtm[x] == '':
        index = varMatch.index(var)
        print var.rjust(6),':',varCalc[index]
    else:
        print var.rjust(6),':',inVarsAtm[x]

'''
#%%
# Loop through input data
for count1,realm in enumerate(data[0:2]):
    realmId    = realm[0]
    modelId    = realm[1]
    fileId     = realm[2]
    dataPath   = realm[3]
    
    # Create input xml file
    command = "".join([uvcdatInstall,'cdscan -x test_',modelId,'_',realmId,'.xml ',dataPath,fileId,'[0-9]*.nc'])
    #print command
    fnull   = open(os.devnull,'w') ; # Create dummy to write stdout output
    p       = subprocess.call(command,stdout=fnull,shell=True)
    fnull.close() ; # Close dummy
    print 'XML spanning file created for model/realm:',modelId,realmId
    
    # Open xml file to read
    infile  = ''.join(['test_',modelId,'_',realmId,'.xml'])
    fIn     = cdm.open(infile)
    
    # Deal with variables
    inVarList       = inVarsAtm ; # Only atmos variables at this stage
    outVarList      = outVarsAtm
    
    # Create output netcdf files
    for count2,var in enumerate(inVarList):
        #print var
        varRead     = var
        varWrite    = outVarList[count2]
        #print 'vars:',varRead,varWrite

        # Assign valid CMIP tableId
        if realmId == 'atmos':
            	tableId = 'Amon'
        else:
            	tableId = 'Omon' ; # placeholder for ocean vars
        
        # Test for PR/RLUT which requires multiple variable manipulation
        if varWrite == 'pr':
            # Deal with PR variable, all other variables are vertically interpolated
            varRead = 'PRECC & PRECL'
            data1   = fIn('PRECC')
            data2   = fIn('PRECL')
            data    = data1+data2 ; #PRECC + PRECL
            data.id = varWrite
            data.long_name = 'precipitation_flux'
            data.history = 'Converted to PR from PRECC+PRECL; Updated units from m/s -> kg m-2 s-1 - Need to check conversion factor'
            data.units  = 'kg m-2 s-1'
        elif varWrite == 'rlut':
            # Deal with RLUT variable, all other variables are vertically interpolated
            varRead = 'FSNTOA & FSNT & FLNT'
            data1   = fIn('FSNTOA')
            data2   = fIn('FSNT')
            data3   = fIn('FLNT')
            data    = data1-data2+data3 ; #FSNTOA - FSNT + FLNT
            data.id = varWrite
            data.long_name = 'toa_outgoing_longwave_flux'
            data.history = 'Converted to RLUT from FSNTOA - FSNT + FLNT'            
            data.units  = data1.units            
        elif varRead == '':
            # Deal with variables requiring interpolation
            index   = varMatch.index(varWrite)
            varRead = varCalc[index][0][0]
            data    = fIn(varRead)
            data.id = varWrite                
        else:
            data    = fIn(varRead)
            data.id = varWrite
        print "".join(['** Writing variable: ',varRead,' to ',varWrite,' **'])
        #e.g. outfile = 'NCAR-CAM5_0p25deg/tas_NCAR-CAM5_0p25deg_Amon_01-12-clim.nc'
        outfile = os.path.join(modelId,"_".join([varWrite,modelId,tableId,'01-12-clim.nc']))
        print "".join(['** Writing file:    ',outfile])
        # Create output directory and purge if exists
        if not os.path.isdir(modelId) and count2 == 0:
            os.makedirs(modelId)
        elif count2 == 0:
            shutil.rmtree(modelId) ; # shutil removes directory and files
            os.makedirs(modelId)
        # Test for existing outfile
        if os.path.isfile(outfile):
            os.remove(outfile) ; # purge existing file
        # Open file and write data
        fOut = cdm.open(outfile,'w')
        fOut.write(data)
        globalAttWrite(fOut,options=None)
        fOut.close()
fIn.close()

# Execute shell command
# source /glade/u/home/durack1/141104_metrics/PCMDI_METRICS/bin/setup_runtime.csh
# > pcmdi_metrics_driver.py -p pcmdi_input_parameters_test.py
