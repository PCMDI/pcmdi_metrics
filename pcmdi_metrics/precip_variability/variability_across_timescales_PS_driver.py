#!/usr/bin/env python

import glob
import os

from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
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
res = param.res
regions_specs = param.regions_specs
fshp = param.region_file
feature = param.feature
attr = param.attr
print(modpath)
print(mod)
print(prd)
print(nperseg, noverlap)
print(res)

# Get flag for CMEC output
cmec = param.cmec

# Create output directory
case_id = param.case_id
outdir_template = param.results_dir
outdir_template = outdir_template.replace("%(mip)",str(mip)).replace("%(case_id)",str(case_id))
for output_type in ["graphics", "diagnostic_results", "metrics_results"]:
    outdir = outdir_template.replace("%(output_type)",output_type)
    os.makedirs(outdir, exist_ok=True)
    print(outdir)

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
        file_list, syr, eyr, dfrq, mip, dat, var, fac, nperseg, noverlap, res, regions_specs, \
        outdir_template, cmec, fshp, feature, attr
    )
