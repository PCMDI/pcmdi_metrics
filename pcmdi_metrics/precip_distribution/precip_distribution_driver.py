#!/usr/bin/env python

import glob
import os
from genutil import StringConstructor
from pcmdi_metrics.driver.pmp_parser import PMPParser
from pcmdi_metrics.precip_distribution.lib import (
    AddParserArgument,
    precip_distribution_frq_amt,
    precip_distribution_cum,
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
res_nxny=str(int(360/res[0]))+"x"+str(int(180/res[1]))
print(modpath)
print(mod)
print(prd)
print(res_nxny)
print('Ref:', ref)

# Get flag for CMEC output
cmec = param.cmec

# Create output directory
case_id = param.case_id
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(str(outdir_template(
    output_type='%(output_type)', mip=mip, case_id=case_id)))

refdir_template = param.process_templated_argument("ref_dir")
refdir = StringConstructor(str(refdir_template(
    output_type='%(output_type)', case_id=case_id)))
refdir = refdir(output_type='diagnostic_results')

for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        try:
            os.makedirs(outdir(output_type=output_type))
        except FileExistsError:
            pass
    print(outdir(output_type=output_type))

# Check data in advance
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

# It is working for daily average precipitation, in units of mm/d, with dimensions of lats, lons, and time.

# Calculate metrics from precipitation frequency and amount distributions
for dat, file in zip(data, file_list):
    precip_distribution_frq_amt(file, dat, prd, var, fac, outdir, cmec)
    
# Calculate metrics from precipitation cumulative distributions
for dat, file in zip(data, file_list):
    precip_distribution_cum(file, dat, prd, var, fac, outdir, cmec)

    