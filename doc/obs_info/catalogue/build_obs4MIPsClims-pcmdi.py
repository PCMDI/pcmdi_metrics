#!/bin/env python

# PJG 01222025 

import gc
import glob
import json
import os
import sys
import time
import datetime
import xcdat as xc

ver = datetime.datetime.now().strftime('v%Y%m%d')

###############################################################

verin = 'v20250113'
vrs = '*'
sea = 'AC'
pathout = './'
pathout = '/p/user_pub/PCMDIobs/catalogue/'

if len(sys.argv) > 1:
    data_path = sys.argv[1]
else:
    data_path = '/p/user_pub/pmp/pmp_reference/obs4MIPs_clims/'

full_path = data_path + '/' + vrs + '/gn/' + verin + '/*_' +sea + '.nc' 

##############################################################3
by_source = {}
by_var = {}

lsttt = glob.glob(full_path)
lstt = []
for l in lsttt:
   path = os.path.dirname(l)
   filename = os.path.basename(l)
   vr = filename.split('_')[0]
   per = filename.split('_')[5]
   source_id = filename.split('_')[2]
   vn = path.split('/')[len(path.split('/'))-1]
   if source_id not in by_source.keys(): by_source[source_id] = {}
   if vr not in by_source[source_id].keys(): by_source[source_id][vr] = {}
   by_source[source_id][vr]['filename'] = filename 
   by_source[source_id][vr]['version'] = vn
   by_source[source_id][vr]['period'] = per 

   if vr not in by_var.keys(): by_var[vr] = {}
   if source_id not in by_var[vr].keys(): by_var[vr][source_id] = {}
   by_var[vr][source_id]['filename'] = filename
   by_var[vr][source_id]['version'] = vn
   by_var[vr][source_id]['period'] = per

with open(pathout + "PMP-obs4MIPsClims-bySource-" + ver + ".json", "w") as outfile:
    outfile.write(json.dumps(by_source, indent=4))
with open(pathout + "PMP-obs4MIPsClims-byVar-" + ver + ".json", "w") as outfile:
    outfile.write(json.dumps(by_var, indent=4))

