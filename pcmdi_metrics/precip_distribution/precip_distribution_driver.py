#!/usr/bin/env python

import copy
import glob
import os

import cdms2 as cdms
import MV2 as MV
from genutil import StringConstructor

from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
from pcmdi_metrics.precip_distribution.lib import (
    AddParserArgument,
    Regrid,
    precip_distribution_cum,
    precip_distribution_frq_amt,
)

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
mip = param.mip
mod = param.mod
var = param.var
modpath = param.modpath
ref = param.ref
prd = param.prd
fac = param.fac
res = param.res
print(modpath)
print(mod)
print(prd)
print(res)
print("Ref:", ref)

# Get flag for CMEC output
cmec = param.cmec

# Create output directory
case_id = param.case_id
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(
    str(outdir_template(output_type="%(output_type)", mip=mip, case_id=case_id))
)

refdir_template = param.process_templated_argument("ref_dir")
refdir = StringConstructor(
    str(refdir_template(output_type="%(output_type)", case_id=case_id))
)
refdir = refdir(output_type="diagnostic_results")

for output_type in ["graphics", "diagnostic_results", "metrics_results"]:
    if not os.path.exists(outdir(output_type=output_type)):
        try:
            os.makedirs(outdir(output_type=output_type))
        except FileExistsError:
            pass
    print(outdir(output_type=output_type))

# Create input file list
file_list = sorted(glob.glob(os.path.join(modpath, "*" + mod + "*")))
data = []
for file in file_list:
    if mip == "obs":
        model = file.split("/")[-1].split(".")[2]
        data.append(model)
    else:
        model = file.split("/")[-1].split(".")[2]
        ens = file.split("/")[-1].split(".")[3]
        data.append(model + "." + ens)
print("Number of datasets:", len(file_list))
print("Dataset:", data)

# Read data -> Regrid -> Calculate metrics
# It is working for daily average precipitation, in units of mm/day, with dimensions of (time,lat,lon)
syr = prd[0]
eyr = prd[1]
for dat, file in zip(data, file_list):
    f = cdms.open(file)
    cal = f[var].getTime().calendar
    if "360" in cal:
        ldy = 30
    else:
        ldy = 31
    print(dat, cal)
    for iyr in range(syr, eyr + 1):
        do = f(
            var,
            time=(str(iyr) + "-1-1 0:0:0", str(iyr) + "-12-" + str(ldy) + " 23:59:59"),
        ) * float(fac)
        # Regridding
        rgtmp = Regrid(do, res)
        if iyr == syr:
            drg = copy.deepcopy(rgtmp)
        else:
            drg = MV.concatenate((drg, rgtmp))
        print(iyr, drg.shape)

    # Calculate metrics from precipitation frequency and amount distributions
    precip_distribution_frq_amt(dat, drg, syr, eyr, res, outdir, ref, refdir, cmec)

    # Calculate metrics from precipitation cumulative distributions
    precip_distribution_cum(dat, drg, cal, syr, eyr, res, outdir, cmec)
