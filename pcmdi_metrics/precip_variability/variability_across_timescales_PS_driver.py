#!/usr/bin/env python

import glob
import os

from genutil import StringConstructor

from pcmdi_metrics.driver.pmp_parser import PMPParser
from pcmdi_metrics.precip_variability.lib import (
    AddParserArgument,
    precip_variability_across_timescale,
)

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
mip = param.mip
mod = param.mod
var = param.var
dfrq = param.frq
modpath = param.modpath
prd = param.prd
fac = param.fac
nperseg = param.nperseg
noverlap = param.noverlap
print(modpath)
print(mod)
print(prd)
print(nperseg, noverlap)

# Get flag for CMEC output
cmec = param.cmec

# Create output directory
case_id = param.case_id
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(
    str(outdir_template(output_type="%(output_type)", mip=mip, case_id=case_id))
)
for output_type in ["graphics", "diagnostic_results", "metrics_results"]:
    if not os.path.exists(outdir(output_type=output_type)):
        try:
            os.makedirs(outdir(output_type=output_type))
        except FileExistsError:
            pass
    print(outdir(output_type=output_type))

# Check data in advance
file_list = sorted(glob.glob(os.path.join(modpath, mod)))
if mip == "obs":
    dat = file_list[0].split("/")[-1].split("_")[2]
else:
    model = file_list[0].split("/")[-1].split("_")[2]
    ens = file_list[0].split("/")[-1].split("_")[4]
    dat = model + "." + ens
print(dat)
print(file_list)   

# Regridding -> Anomaly -> Power spectra -> Domain&Frequency average -> Write
syr = prd[0]
eyr = prd[1]
precip_variability_across_timescale(
        file_list, syr, eyr, dfrq, mip, dat, var, fac, nperseg, noverlap, outdir, cmec
    )
