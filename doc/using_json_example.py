#!/bin/env python

###############################################
# PURPOSE: PROVIDE EXAMPLES OF HOW TO READ AND MANIPULATE PYTHON DICTIONARIES
# LOADED FROM DEMO JSON FILES THAT HAVE BEEN PRODUCED BY PCMDI'S METRICS PACKAGE.
#
# Peter Gleckler, PCMDI/LLNL
# Last update:  7/19/16

###############################################

import json
import os,sys
import pcmdi_metrics

# READ JSON FILE CONTAING RESULTS FROM DEMO DATABASE

## LOCATION OF DEMO JSON FILES
cmipmods_file =  os.path.join(
        pcmdi_metrics.__path__[0],
        "..",
        "..",
        "..",
        "..",
        "demo/results/rlut_2.5x2.5_esmf_linear_metrics.json")

# LOADING A DICTIONARY INTO MEMORY FROM A JSON FILE

cmipmods_dic = json.load(open(cmipmods_file, 'rb'))


# PCMDI METRICS PACKAGE STORES INFORMATION IN NESTED DICTIONARIES. WE
# START WITH SIMPLE EXAMPLE.

sample_result = cmipmods_dic['RESULTS']['Mod_1']['defaultReference']['r1i1p1']['global']['rms_xy_ann_TROPICS']

print ''
print 'A sample result: ', sample_result 
print ''

print 'Using "type" function to show conversion of test1 from unicode to real via float(sample_result) ', \
    type(sample_result), '  ', type(float(sample_result))

# FOR BASIC INFORMATION ON PYTHON DICTIONARIES SEE
# http://www.tutorialspoint.com/python/python_dictionary.htm

KeyList = cmipmods_dic.keys()
print ''
print 'Keys from from dictionary read from json file ', KeyList
print ''
#
KeyList = [s.encode('utf-8')
           for s in KeyList]  # CHANGE FROM UNICODE TO BYTE STRINGS

print 'Keys from from dictionary read from json file after unicode converted to strings ', KeyList
KeyList

print ''

print 'Getting a list from all models in the CMIP database: ', cmipmods_dic['RESULTS'].keys()

# NOTE CONVERTING FROM UNICODE TO BYTE STRINGS IS NOT NECESSARY WHEN
# ACCESSING KEYS IN DICTIONARIES. EITHER UNICODE OR ASCII CAN BE USED.


