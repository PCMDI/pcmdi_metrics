#!/bin/env python

###############################################
# PURPOSE: PROVIDE EXAMPLES OF HOW TO READ AND MANIPULATE PYTHON DICTIONARIES
# LOADED FROM JSON FILES THAT HAVE BEEN PRODUCED BY PCMDI'S METRICS PACKAGE.

# Peter Gleckler, PCMDI/LLNL
# Last update:  7/30/14

###############################################

import json

# READ JSON FILE CONTAING RESULTS FROM ONE MODEL
onemod_file = '/work/gleckler1/processed_data/metrics_package/' +\
    'metrics_results/sampletest1/tas_2.5x2.5_regrid2_linear_metrics.json'

# READ JSON FILE CONTAING RESULTS FROM A CMIP DATABASE
cmipmods_file = '/work/gleckler1/processed_data/metrics_package/' +\
    'metrics_results/cmip5_test/tas_2.5x2.5_regrid2_linear_metrics.json'

# HOW TO LOAD A DICTIONARY INTO MEMORY FROM A JSON FILE

onemod_dic = json.load(open(onemod_file, 'rb'))
cmipmods_dic = json.load(open(cmipmods_file, 'rb'))


# PCMDI METRICS PACKAGE STORES INFORMATION IN NESTED DICTIONARIES. WE
# START WITH SIMPLE EXAMPLE.

print ''

test1 = onemod_dic['CCSM4']['default']['r1i1p1']['global']['rms_xy_ann_GLB']

print 'A sample result: ', test1
print ''
print 'Using "type" function to show conversion of test1 from unicode to real via float(test1) ', \
    type(test1), '  ', type(float(test1))


print ''
print 'Showing the source of the "default" observations: ', onemod_dic['CCSM4']['default']['source']

# FOR BASIC INFORMATION ON PYTHON DICTIONARIES SEE
# http://www.tutorialspoint.com/python/python_dictionary.htm

KeyList = onemod_dic.keys()
print ''
print 'Keys from from dictionary read from json file ', KeyList
print ''
#
KeyList = [s.encode('utf-8')
           for s in KeyList]  # CHANGE FROM UNICODE TO BYTE STRINGS

print 'Keys from from dictionary read from json file after unicode converted to strings ', KeyList
KeyList

print ''

print 'Getting a list from all models in the CMIP database: ', cmipmods_dic.keys()

# NOTE CONVERTING FROM UNICODE TO BYTE STRINGS IS NOT NECESSARY WHEN
# ACCESSING KEYS IN DICTIONARIES. EITHER UNICODE OR ASCII CAN BE USED.
