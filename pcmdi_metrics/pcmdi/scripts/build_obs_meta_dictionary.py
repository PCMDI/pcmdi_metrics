#!/bin/env python

# PJG 10212014 NOW INCLUDES SFTLF FROM
# PJG 02012016 RESURRECTING...
# /obs AND HARDWIRED TEST CASE WHICH
# NEEDS FIXIN
# PJD 171121 Attempting to fix issue with default missing for thetao and
# CMOR Table being wrong

import cdms2
import gc
import glob
import json
import os
import sys
import time

if len(sys.argv) > 1:
    data_path = sys.argv[1]
else:
    data_path = "/work/gleckler1/processed_data/obs"

lst = glob.glob(os.path.join(data_path, "*/mo/*/*/ac/*.nc"))
data_path_fx = "/clim_obs/obs"
lstm = glob.glob(os.path.join(data_path_fx, "fx/sftlf/*.nc"))
lst.extend(lstm)
del lstm
del (data_path, data_path_fx)
gc.collect()
# Generate remap dictionary
sftlf_product_remap = {
    "ECMWF-ERAInterim": "ERAINT",
    "ECMWF-ERA40": "ERA40",
    "NCAR-JRA25": "JRA25",
}

# FOR MONTHLY MEAN OBS
obs_dic_in = {
    "rlut": {"default": "CERES"},
    "rst": {"default": "CERES"},
    "rsut": {"default": "CERES"},
    "rsds": {"default": "CERES"},
    "rlds": {"default": "CERES"},
    "rsdt": {"default": "CERES"},
    "rsdscs": {"default": "CERES"},
    "rldscs": {"default": "CERES"},
    "rlus": {"default": "CERES"},
    "rsus": {"default": "CERES"},
    "rlutcs": {"default": "CERES"},
    "rsutcs": {"default": "CERES"},
    "rstcre": {"default": "CERES"},
    "rltcre": {"default": "CERES"},
    "pr": {"default": "GPCP", "alternate1": "TRMM"},
    "prw": {"default": "RSS"},
    "tas": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "psl": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "ua": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "va": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "uas": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "hus": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "vas": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "ta": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "zg": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "tauu": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "tauv": {"default": "ERAINT", "alternate2": "JRA25", "alternate1": "ERA40"},
    "tos": {"default": "UKMETOFFICE-HadISST-v1-1"},
    "zos": {"default": "CNES-AVISO-L4"},
    "sos": {"default": "NODC-WOA09"},
    "ts": {"default": "HadISST1"},
    "thetao": {
        "default": "WOA13v2",
        "alternate1": "UCSD",
        "alternate2": "Hosoda-MOAA-PGV",
        "alternate3": "IPRC",
    },
}

obs_dic = {}

for filePath in lst:
    if "clim_obs" in filePath:
        subp = os.path.join(*filePath.split("/")[3:])
        fileName = subp.split("/")[-1]
        realm = filePath.split("/")[3:][0]
        var = filePath.split("/")[3:][1]
        product = filePath.split("/")[3:][2].split("_")[3]
        # Remap sftlf
        product = sftlf_product_remap.get(product, product)
    elif "gleckler1" in filePath:
        subp = filePath.split("obs")[1]
        realm = subp.split("/")[1]
        var = subp.split("/")[3]
        product = subp.split("/")[4]

    # Assign tableId
    if realm == "atm":
        tableId = "Amon"
    elif realm == "ocn":
        tableId = "Omon"
    elif realm == "fx":
        tableId = "fx"
    print("tableId:", tableId)
    print("subp:", subp)
    print("var:", var)
    print("product:", product)

    fileName = subp.split("/")[-1]
    print("Filename:", fileName)
    # Fix rgd2.5_ac issue
    fileName = fileName.replace("rgd2.5_ac", "ac")
    if "-clim" in fileName:
        period = fileName.split("_")[-1]
    # Fix durack1 formatted files
    elif "sftlf_pcmdi-metrics_fx" in fileName:
        period = fileName.split("_")[-1]
        period = period.replace(".nc", "")
    else:
        period = fileName.split("_")[-2]
    period = period.replace("-clim.nc", "")  # .replace('ac.nc','')
    print("period:", period)

    # TRAP FILE NAME FOR OBS DATA
    if var not in list(obs_dic.keys()):
        obs_dic[var] = {}
    if product not in list(obs_dic[var].keys()) and os.path.isfile(filePath):
        obs_dic[var][product] = {}
        obs_dic[var][product]["filename"] = fileName
        obs_dic[var][product]["CMIP_CMOR_TABLE"] = tableId
        obs_dic[var][product]["period"] = period
        obs_dic[var][product]["RefName"] = product
        obs_dic[var][product]["RefTrackingDate"] = time.ctime(
            os.path.getmtime(filePath.strip())
        )
        md5 = os.popen("md5sum " + filePath)
        md5 = md5.readlines()[0].split()[0]
        obs_dic[var][product]["MD5sum"] = md5
        f = cdms2.open(filePath)
        d = f(var)
        shape = d.shape
        f.close()
        shape = repr(d.shape)
        obs_dic[var][product]["shape"] = shape
        print("md5:", md5)
        print("")
        del (d, fileName)
        gc.collect()

    try:
        for r in list(obs_dic_in[var].keys()):
            # print '1',r,var,product
            # print obs_dic_in[var][r],'=',product
            if obs_dic_in[var][r] == product:
                # print '2',r,var,product
                obs_dic[var][r] = product
    except BaseException:
        pass
del (filePath, lst, md5, period, product, r, realm, shape, subp, tableId, var)
gc.collect()
# pdb.set_trace()

# ADD SPECIAL CASE SFTLF FROM TEST DIR
product = "UKMETOFFICE-HadISST-v1-1"
var = "sftlf"
obs_dic[var][product] = {}
obs_dic[var][product]["CMIP_CMOR_TABLE"] = "fx"
obs_dic[var][product]["shape"] = "(180, 360)"
obs_dic[var][product][
    "filename"
] = "sftlf_pcmdi-metrics_fx_UKMETOFFICE-HadISST-v1-1_198002-200501-clim.nc"
obs_dic[var][product]["RefName"] = product
obs_dic[var][product]["MD5sum"] = ""
obs_dic[var][product]["RefTrackingDate"] = ""
obs_dic[var][product]["period"] = "198002-200501"
del (product, var)
gc.collect()

# Save dictionary locally and in doc subdir
json_name = "obs_info_dictionary.json"
json.dump(
    obs_dic, open(json_name, "wb"), sort_keys=True, indent=4, separators=(",", ": ")
)
json.dump(
    obs_dic,
    open("../../../../doc/" + json_name, "wb"),
    sort_keys=True,
    indent=4,
    separators=(",", ": "),
)
