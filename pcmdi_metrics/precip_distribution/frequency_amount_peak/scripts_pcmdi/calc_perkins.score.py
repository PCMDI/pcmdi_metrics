import cdms2 as cdms
import MV2 as MV
import numpy as np
import pcmdi_metrics
import glob
import os
from pcmdi_metrics.driver.pmp_parser import PMPParser
with open('../lib/argparse_functions.py') as source_file:
    exec(source_file.read())
with open('../lib/lib_dist_freq_amount_peak_width.py') as source_file:
    exec(source_file.read())

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
ref = param.ref
modpath = param.modpath
outpath = param.results_dir
print('reference: ', ref)
print('modpath: ', modpath)
print('outdir: ', outpath)

# Get flag for CMEC output
cmec = param.cmec

var = 'pdf'
res = '90x45'
# res = '180x90'
# res = '360x180'
# res = '720x360'

# Read reference data
dist_ref = cdms.open(ref)[var]
dat_ref = ref.split("/")[-1].split("_")[-1].split(".")[0]

# Read -> Calculate Perkins score -> Domain average -> Write
metrics = {'RESULTS': {}}
file_list = sorted(glob.glob(os.path.join(
    modpath, 'dist_freq.amount_regrid.'+res+'_*.nc')))
#     modpath, 'dist_freq.amount_regrid.'+res+'_*E3SM-1-0*.nc')))

for model in file_list:
    dist_mod = cdms.open(model)[var]
    ver = model.split("/")[6]
    mip = model.split("/")[9]
    if mip == 'obs':
        mod = model.split("/")[-1].split("_")[-1].split(".")[0]
        dat = mod
    else:
        mod = model.split("/")[-1].split("_")[-1].split(".")[0]
        ens = model.split("/")[-1].split("_")[-1].split(".")[1]
        dat = mod + '.' + ens

    perkins_score = np.sum(np.minimum(dist_ref, dist_mod), axis=1)
    perkins_score = MV.array(perkins_score)
    perkins_score.setAxisList(
        (dist_ref.getAxis(0), dist_ref.getAxis(2), dist_ref.getAxis(3)))

    metrics['RESULTS'][dat] = {}
    metrics['RESULTS'][dat]['pscore'] = AvgDomain(perkins_score)

    # Write data (nc file for spatial pattern of Perkins score)
    if mip == 'obs':
        outdir = os.path.join(outpath, 'diagnostic_results',
                              'precip_distribution', mip, ver)
    else:
        outdir = os.path.join(outpath, 'diagnostic_results',
                              'precip_distribution', mip, 'historical', ver)
    outfilename = "dist_freq_pscore_regrid."+res+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir, outfilename), "w") as out:
        out.write(perkins_score, id="pscore")

    # Write data (json file for area averaged metrics)
    if mip == 'obs':
        outdir = os.path.join(outpath, 'metrics_results',
                              'precip_distribution', mip, ver)
    else:
        outdir = os.path.join(
            outpath, 'metrics_results', 'precip_distribution', mip, 'historical', ver)
    outfilename = "dist_freq_pscore_area.mean_regrid."+res+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(outdir, outfilename)
    JSON.write(metrics,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))

    print('Complete ', mip, dat)
print('Complete all')
