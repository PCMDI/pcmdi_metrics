#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 17:42:30 2016

@author: durack1
"""

import subprocess
import sys
import os
#import shlex

# Platform
platform = os.uname()
platformId = [platform[0], platform[2], platform[1]]
osAccess = [os.access('/', os.W_OK), os.access('/', os.R_OK)]
print 'platformId',platformId
print 'osAccess',osAccess
print '---'

p = subprocess.Popen('conda info', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) #cwd='./',
out = p.stdout.read()
#print 'stdout', out
stde = p.stderr.read()

p.terminate()
if stde != '':
    print 'error encountered'
    sys.exit()

pairs = {
         'condaPlatform':'platform',
         'condaVersion':'conda version',
         'condaIsPrivate':'conda is private',
         'condaenvVersion':'conda-env version',
         'condabuildVersion':'conda-build version',
         'condaPythonVersion':'python version',
         'condaRootEnvironment':'root environment',
         'condaDefaultEnvironment':'default environment'
         }

for count,strBit in enumerate(iter(out.splitlines())):
    for count1,pairKey in enumerate(pairs):
        if pairs[pairKey] in strBit:
            vars()[pairKey] = strBit.replace(''.join([pairs[pairKey],' :']),'').strip()

for count,pair in enumerate(pairs):
    print pair,eval(pair)
print '---'

pairs = {
         'PMPVersion':'pcmdi_metrics-',
         'PMPObsVersion':'',
         'CDPVersion':'cdp-',
         'cdmsVersion':'cdms2-',
         'cdtimeVersion':'cdtime-',
         'cdutilVersion':'cdutil-',
         'ESMFVersion':'esmf-ESMF_',
         'genutilVersion':'genutil-',
         'matplotlibVersion':'matplotlib-',
         'numpyVersion':'numpy-',
         'pythonVersion':'python-',
         'regrid2Version':'',
         'VCSVersion':'vcs-',
         'VTKVersion':'vtk-cdat-'
         }

condaMetaDir = os.path.join(condaDefaultEnvironment,'conda-meta')
listScour = os.listdir(condaMetaDir)
for count,strBit in enumerate(listScour):
    for count1,pairKey in enumerate(pairs):
        if pairs[pairKey] in ['']:
            vars()[pairKey] = 'None' ; # Case unimplemented
        elif pairs[pairKey] in strBit:
            vars()[pairKey] = strBit.replace(pairs[pairKey],'').replace('.json','')
        else:
            vars()[pairKey] = 'None' ; # Case uninstalled

# Sort
keyList = pairs.keys()
keyList.sort()
# Print
for count,key in enumerate(keyList):
    print key,eval(key)