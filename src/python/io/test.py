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

def populate_prov(prov,cmd,pairs,sep=None,index=1,fill_missing=False):
    try:
        p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        return
    out,stde = p.communicate()
    if stde != '':
        print 'Error encountered - valid conda installation not on path'
        sys.exit()
    for strBit in out.splitlines():
        for key, value in pairs.iteritems():
            if value in strBit:
                print strBit.split(sep)
                prov[key] = strBit.split(sep)[index].strip()
    if fill_missing is not False:
        for k in pairs:
            if not prov.has_key(k):
                prov[k] = fill_missing
    return

prov = {}
platform = os.uname()
prov["platformId"] = [platform[0], platform[2], platform[1]]
prov["userId"] = pwd.getpwuid(os.getuid()).pw_name
prov["osAccess"] = bool(os.access('/', os.W_OK) * os.access('/', os.R_OK))

prov["conda"]={}
pairs = {
         'Platform':'platform ',
         'Version':'conda version ',
         'IsPrivate':'conda is private ',
         'envVersion':'conda-env version ',
         'buildVersion':'conda-build version ',
         'PythonVersion':'python version ',
         'RootEnvironment':'root environment ',
         'DefaultEnvironment':'default environment '
         }
populate_prov(prov["conda"],"conda info",pairs,sep=":",index=-1)
pairs = {
         'PMP':'pcmdi_metrics ',
         'PMPObs':'pcmdi_metrics_obs ',
         'CDP':'cdp ',
         'cdms':'cdms2 ',
         'cdtime':'cdtime ',
         'cdutil':'cdutil ',
         'ESMF':'esmf-ESMF ',
         'genutil':'genutil ',
         'matplotlib':'matplotlib ',
         'numpy':'numpy ',
         'python':'python ',
         'VCS':'vcs ',
         'VTK':'vtk-cdat '
         }
prov["packages"]={}
populate_prov(prov["packages"],"conda list",pairs,fill_missing=None) 
# TRying to capture glxinfo

pairs = {
        "vendor" : "OpenGL vendor string",
        "renderder": "OpenGL renderer string",
        "version" : "OpenGL version string",
        "shading language version": "OpenGL shading language version string",
        "glxServerVendor" :"server glx vendor string",
        "glxServerVersion" : "server glx version string",
        "glxClientVendor": "client glx vendor string",
        "glxClientVersion": "client glx version string",
        "GLXVersion" : "GLX version",
        "ESVersion": "OpenGL ES profile version string",
        "ESShadingLanguage" : "OpenGL ES profile shading language version string",
        }

prov["openGL"]={}
populate_prov(prov["openGL"],"glxinfo",pairs,sep=":",index=-1)
print prov
