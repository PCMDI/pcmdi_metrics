#!/usr/bin/env python

import copy
import glob
import os

import MV2 as MV
from genutil import StringConstructor

from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
from pcmdi_metrics.precip_distribution.lib import ( 
    AddParserArgument,
    Regrid,
    precip_distribution_cum,
    precip_distribution_frq_amt,
)

import xarray as xr
import xcdat

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
mip = param.mip
mod = param.mod
var = param.var
frq = param.frq
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

# Read data -> Regrid -> Calculate metrics
# It is working for daily average precipitation, in units of mm/day, with dimensions of (time,lat,lon)
file_list = sorted(glob.glob(os.path.join(modpath, mod)))
print(file_list)
# f = xcdat.open_mfdataset(file_list)
f = xr.open_mfdataset(file_list)

if mip == "obs":
    if file_list[0].split("/")[-1].split("_")[2] == "reanalysis":
        dat = file_list[0].split("/")[-1].split("_")[3]
    else:
        dat = file_list[0].split("/")[-1].split("_")[2]
else:
    model = file_list[0].split("/")[-1].split("_")[2]
    ens = file_list[0].split("/")[-1].split("_")[4]
    dat = model + "." + ens

cal = f.time.encoding["calendar"]
print(dat, cal)

if "360" in cal:
    ldy = 30
else:
    ldy = 31

syr = prd[0]
eyr = prd[1]
for iyr in range(syr, eyr + 1):
    do = f.sel(
        time=slice(
            str(iyr) + "-01-01 00:00:00", str(iyr) + "-12-" + str(ldy) + " 23:59:59"
        )
    )[var]
    # Correct negative precip to 0 (ERA-interim from CREATE-IP and ERA-5 from obs4MIP have negative precip values between -1 and 0)
    do = xr.where((do < 0) & (do > -1), 0, do)
    do = xr.DataArray.to_cdms2(do) * float(fac)

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
