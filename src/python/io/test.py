#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 17:42:30 2016

@author: durack1
"""

import os
import pwd
import re
import subprocess
import sys
import shlex

# Platform
platform = os.uname()
platformId = [platform[0], platform[2], platform[1]]
userId = pwd.getpwuid(os.getuid()).pw_name
osAccess = bool(os.access('/', os.W_OK) * os.access('/', os.R_OK))

p = subprocess.Popen(shlex.split('conda info'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)#, shell=True) #cwd='./',
out,stde = p.communicate()
if stde != '':
    print 'Error encountered - valid conda installation not on path'
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
print out
sys.exit()
for count,strBit in enumerate(iter(out.splitlines())):
    for count1,pairKey in enumerate(pairs):
        if pairs[pairKey] in strBit:
            vars()[pairKey] = strBit.replace(''.join([pairs[pairKey],' :']),'').strip()

for count,key in enumerate(pairs):
    print key,eval(key)
print '---'

pairs = {
         'PMPVersion':'pcmdi_metrics-',
         'PMPObsVersion':'pcmdi_metrics_obs-',
         'CDPVersion':'cdp-',
         'cdmsVersion':'cdms2-',
         'cdtimeVersion':'cdtime-',
         'cdutilVersion':'cdutil-',
         'ESMFVersion':'esmf-ESMF_',
         'genutilVersion':'genutil-',
         'matplotlibVersion':'matplotlib-',
         'numpyVersion':'numpy-',
         'pythonVersion':'python-',
         'VCSVersion':'vcs-',
         'VTKVersion':'vtk-cdat-'
         }

condaMetaDir = os.path.join(condaDefaultEnvironment,'conda-meta')
listScour = os.listdir(condaMetaDir) ; listScour.sort()
for count,pairKey in enumerate(pairs):
    for count1,strBit in enumerate(listScour):
        test = re.search(''.join(['^',pairs[pairKey]]),strBit)
        if test is not None:
            vars()[pairKey] = strBit.replace(pairs[pairKey],'').replace('.json','')
            break
        else:
            vars()[pairKey] = 'None' ; # Case uninstalled

# Sort
keyList = pairs.keys()
keyList.sort()
# Print
for count,key in enumerate(keyList):
    print key,eval(key)
