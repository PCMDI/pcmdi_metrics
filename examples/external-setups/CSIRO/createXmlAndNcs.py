#!/short/p66/pjd599/PCMDI_METRICS/v1p0/bin/python

"""
Created on Mon Jan 19 20:26:30 2015

Paul J. Durack 20th January 2015

This script scans netcdf files to create a composite xml spanning file
and then using this index file, writes netcdf files for each variable

@author: durack1
"""

import gc
import os
import shutil
import subprocess  # ,sys
import cdms2 as cdm
import cdutil as cdu
from string import replace

# Set cdms preferences - no compression, no shuffling, no complaining
cdmsFlag = 1
cdm.setNetcdfDeflateFlag(cdmsFlag)
cdm.setNetcdfDeflateLevelFlag(9)
cdm.setNetcdfShuffleFlag(0)
cdm.setCompressionWarnings(0)
# cdm.axis.level_aliases.append('zt') ; # Add zt to axis list
# cdm.axis.latitude_aliases.append('yh') ; # Add yh to axis list
# cdm.axis.longitude_aliases.append('xh') ; # Add xh to axis list
# Set bound automagically
# cdm.setAutoBounds(1) ; # Use with caution

# Set build info once
buildVersion = 'v1p0'

# Create input variable lists
uvcdatInstall = ''.join(
    ['/short/p66/pjd599/PCMDI_METRICS/', buildVersion, '/bin/'])

inDataPath = '/g/data/ua6/drstree/CMIP5/GCM/CSIRO-BOM/_MODEL_/_EXPERIMENT_/mon/_REALM_/_VAR_/r1i1p1/'
inModels = ['ACCESS1-0', 'ACCESS1-3', ]
inExperiments = ['piControl', ]
inRealms = ['atmos', 'fx', 'ocean', ]
inVars = [['pr',
           'psl',
           'rlut',
           'rlutcs',
           'rsut',
           'rsutcs',
           'ta',
           'tas',
           'ua',
           'uas',
           'va',
           'vas',
           'zg'],
          ['sftlf'],
          ['sos',
           'tos'],
          ]
# Depending on the 'indicator' settings below the year 529 will be
# excluded (or included) from calculations
inTimes = [500, 529]

# Do some housekeeping - force purge existing files
pathBits = ['ncs', 'xmls']
for path in pathBits:
    if os.path.isdir(path):
        shutil.rmtree(path)
        os.mkdir(path)
    else:
        os.mkdir(path)

for count1, modelId in enumerate(inModels):
    for count2, experimentId in enumerate(inExperiments):
        for count3, realmId in enumerate(inRealms):
            for count4, varId in enumerate(inVars[count3]):
                # print modelId,experimentId,realmId,varId
                # Deal with realms and realm-dependent paths
                if realmId == 'atmos':
                    tableId = 'Amon'
                elif realmId == 'fx':
                    tableId = 'fx'
                else:
                    tableId = 'Omon'
                # Replace path components with loop/variable inputs
                if tableId == 'fx':
                    dataPath = '/g/data/ua6/drstree/CMIP5/GCM/CSIRO-BOM/' +\
                        '_MODEL_/_EXPERIMENT_/_REALM_/atmos/_VAR_/r0i0p0/'
                else:
                    dataPath = inDataPath
                dataPath = replace(dataPath, '_MODEL_', modelId)
                dataPath = replace(dataPath, '_EXPERIMENT_', experimentId)
                dataPath = replace(dataPath, '_REALM_', realmId)
                dataPath = replace(dataPath, '_VAR_', varId)
                # Create input xml files
                outFileXml = ''.join(['xmls/',
                                      varId,
                                      '_',
                                      modelId,
                                      '_',
                                      experimentId,
                                      '_',
                                      realmId,
                                      '.xml'])
                command = ''.join([uvcdatInstall,
                                   'cdscan -x ',
                                   outFileXml,
                                   ' ',
                                   dataPath,
                                   varId,
                                   '*.nc'])
                # print command
                fnull = open(
                    os.devnull,
                    'w')  # Create dummy to write stdout output
                p = subprocess.call(command, stdout=fnull, shell=True)
                fnull.close()  # Close dummy
                print 'XML spanning file created for model/experiment/realm/var:', modelId, experimentId, realmId, varId
                # continue

                # Open xml file to read
                fIn = cdm.open(outFileXml)
                # Create output variables
                # print varId,str(inTimes[0]),str(inTimes[-1]+1)
                if realmId == 'fx':
                    data = fIn[varId]
                    # print data.shape
                else:
                    # String specifies 'years' or componentTime - indexed are
                    # offset by one (within bounds)
                    data = fIn[varId](
                        time=(str(inTimes[0]), str(inTimes[-1] + 1), 'con'))
                    # print data.shape
                    # print data.getTime().asComponentTime()[0]
                    # print data.getTime().asComponentTime()[-1]
                    # Calculate seasonal climatology
                    data = cdu.ANNUALCYCLE.climatology(data)
                    # print data.shape
                inTimeStr = "-".join([''.join([(format(inTimes[0], '04d')), '01']), ''.join(
                    [(format(inTimes[1], '04d')), '12'])])
                data.astype('float32')
                data.id = varId
                print "".join(['** Writing variable: ', varId, ' **'])
                if realmId == 'fx':
                    outfile = ''.join(
                        ['ncs/', '_'.join([varId, modelId, experimentId, tableId, 'r0i0p0.nc'])])
                else:
                    # outfile =
                    # ncs/tas_ACCESS1-0_piControl_Amon_r1i1p1_050001-052912-clim.nc
                    outfile = ''.join(['ncs/',
                                       '_'.join([varId,
                                                 modelId,
                                                 experimentId,
                                                 tableId,
                                                 'r1i1p1',
                                                 inTimeStr]),
                                       '-clim.nc'])
                print "".join(['** Writing file    : ', outfile])
                # Create output netcdf files
                if os.path.isfile(outfile):
                    os.remove(outfile)  # purge existing file
                fOut = cdm.open(outfile, 'w')
                fOut.write(data)
                fOut.close()
                fIn.close()
                del(data)
                gc.collect()

# Execute shell command
# source /short/p66/pjd599/PCMDI_METRICS/v1p0/bin/setup_runtime.csh
# > pcmdi_metrics_driver.py -p gfdl_input_parameters_test.py
