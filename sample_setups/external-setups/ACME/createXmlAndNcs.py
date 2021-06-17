#!/export/durack1/141126_pcmdi_metrics/PCMDI_METRICS/bin/python

"""
Created on Wed Nov 26 13:55:18 2014

Paul J. Durack 26th November 2014

This script scans netcdf files to create a composite xml spanning file
and then using this index file, writes netcdf files for each variable

@author: durack1
"""

# Python module imports
import os
import shutil
import subprocess
import sys
import cdms2 as cdm
# Add durolib to path
sys.path.insert(1, '/export/durack1/git/pylib')  # Assumes crunchy/oceanonly
from durolib import globalAttWrite


# Set cdms preferences - no compression, no shuffling, no complaining
cdm.setNetcdfDeflateFlag(1)
# 1-9, min to max - Comes at heavy IO (read/write time cost)
cdm.setNetcdfDeflateLevelFlag(9)
cdm.setNetcdfShuffleFlag(0)
cdm.setCompressionWarnings(0)  # Turn off nag messages
# Set bounds automagically
# cdm.setAutoBounds(1) ; # Use with caution

# Set build info once
buildDate = '141126'
outPath = '/work/durack1/Shared/141126_metrics-acme'
# Create input variable lists
uvcdatInstall = ''.join(
    ['/export/durack1/', buildDate, '_pcmdi_metrics/PCMDI_METRICS/bin/'])
# Specify inputs:
#        Realm   ModelId               InputFiles    SourceDirectory
data = [
    ['atmos',
     'ACME-CAM5-SE_v0pt1',
     'B1850C5e1_ne30_',
     '/work/durack1/Shared/141126_metrics-acme/'],
]
inVarsAtm = [
    '',
    '',
    'TMQ',
    'PSL',
    'FLDS',
    '',
    'FLUTC',
    'FSDS',
    'FSDSC',
    'SOLIN',
    '',
    'TREFHT',
    'TAUX',
    'TAUY',
    '',
    '',
    '']  # FLDSC, QREFHT not available
outVarsAtm = ['hus', 'pr', 'prw', 'psl', 'rlds', 'rlut', 'rlutcs', 'rsds', 'rsdscs', 'rsdt',
              'ta', 'tas', 'tauu', 'tauv', 'ua', 'va', 'zg']  # huss,uas,vas not available
varMatch = [
    'hus',
    'pr',
    'rlut',
    'ta',
    'ua',
    'va',
    'zg']  # uas, vas not available
varCalc = [[['Q',
             'PS'],
            'Q interpolated to standard plevs'],
           [['PRECC',
             'PRECL'],
            'PRECC + PRECL and unit conversion'],
           [['FSNTOA',
             'FSNT',
             'FLNT'],
            'FSNTOA-FSNT+FLNT'],
           [['T',
             'PS'],
            'T interpolated to standard plevs'],
           [['U',
             'PS'],
            'U interpolated to standard plevs'],
           [['V',
             'PS'],
            'V interpolated to standard plevs'],
           [['Z3',
             'PS'],
            'Z3 interpolated to standard plevs']]
inVarsOcn = ['SALT', 'TEMP', 'SSH']
outVarsOcn = ['sos', 'tos', 'zos']

# Loop through input data
for count1, realm in enumerate(data[0:2]):
    realmId = realm[0]
    modelId = realm[1]
    fileId = realm[2]
    dataPath = realm[3]

    # Create input xml file
    command = "".join([uvcdatInstall,
                       'cdscan -x test_',
                       modelId,
                       '_',
                       realmId,
                       '.xml ',
                       dataPath,
                       fileId,
                       '[0-9]*.nc'])
    # print command
    fnull = open(os.devnull, 'w')  # Create dummy to write stdout output
    p = subprocess.call(command, stdout=fnull, shell=True)
    fnull.close()  # Close dummy
    print 'XML spanning file created for model/realm:', modelId, realmId
    # sys.exit()

    # Open xml file to read
    infile = ''.join(['test_', modelId, '_', realmId, '.xml'])
    fIn = cdm.open(infile)

    # Deal with variables
    inVarList = inVarsAtm  # Only atmos variables at this stage
    outVarList = outVarsAtm

    # Create output netcdf files
    for count2, var in enumerate(inVarList):
        # print var
        varRead = var
        varWrite = outVarList[count2]
        # print 'vars:',varRead,varWrite

        # Assign valid CMIP tableId
        if realmId == 'atmos':
            tableId = 'Amon'
        else:
            tableId = 'Omon'  # placeholder for ocean vars

        # Test for PR/RLUT which requires multiple variable manipulation
        if varWrite == 'pr':
            # Deal with PR variable, all other variables are vertically
            # interpolated
            varRead = 'PRECC & PRECL'
            data1 = fIn('PRECC')
            data2 = fIn('PRECL')
            data = data1 + data2  # PRECC + PRECL
            data.id = varWrite
            data.long_name = 'precipitation_flux'
            data.history = 'Converted to PR from PRECC+PRECL; Updated units from m/s -> ' +\
                'kg m-2 s-1 - Need to check conversion factor'
            data.units = 'kg m-2 s-1'
        elif varWrite == 'rlut':
            # Deal with RLUT variable, all other variables are vertically
            # interpolated
            varRead = 'FSNTOA & FSNT & FLNT'
            data1 = fIn('FSNTOA')
            data2 = fIn('FSNT')
            data3 = fIn('FLNT')
            data = data1 - data2 + data3  # FSNTOA - FSNT + FLNT
            data.id = varWrite
            data.long_name = 'toa_outgoing_longwave_flux'
            data.history = 'Converted to RLUT from FSNTOA - FSNT + FLNT'
            data.units = data1.units
        elif varRead == '':
            # Deal with variables requiring interpolation
            index = varMatch.index(varWrite)
            varRead = varCalc[index][0][0]
            data = fIn(varRead)
            data.id = varWrite
        else:
            data = fIn(varRead)
            data.id = varWrite
        print "".join(['** Writing variable: ', varRead, ' to ', varWrite, ' **'])
        # e.g. outfile = 'ACME-CAM5-SE_v0.0.1/tas_ACME-CAM5-SE_v0.0.1_Amon_01-12-clim.nc'
        outfile = os.path.join(
            outPath, modelId, "_".join([varWrite, modelId, tableId, '01-12-clim.nc']))
        print "".join(['** Writing file:    ', outfile])
        # Create output directory and purge if exists
        if not os.path.isdir(os.path.join(outPath, modelId)) and count2 == 0:
            os.makedirs(modelId)
        elif count2 == 0:
            shutil.rmtree(
                os.path.join(
                    outPath,
                    modelId))  # shutil removes directory and files
            os.makedirs(os.path.join(outPath, modelId))
        # Test for existing outfile
        if os.path.isfile(outfile):
            os.remove(outfile)  # purge existing file
        # Open file and write data
        fOut = cdm.open(outfile, 'w')
        fOut.write(data)
        globalAttWrite(fOut, options=None)
        fOut.close()
fIn.close()

# Execute shell command
# source /export/durack1/141126_metrics/PCMDI_METRICS/bin/setup_runtime.csh
# > pcmdi_metrics_driver.py -p pcmdi_input_parameters_test.py
