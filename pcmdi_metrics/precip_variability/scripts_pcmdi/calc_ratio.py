import json
import glob
import copy
import os
from pcmdi_metrics.driver.pmp_parser import PMPParser
from pcmdi_metrics.precip_variability.lib import AddParserArgument

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
ref = param.ref
modpath = param.modpath
outdir = param.results_dir
print('reference: ', ref)
print('modpath: ', modpath)
print('outdir: ', outdir)

# Read reference data for ratio
psdmfm_ref = json.load(open(ref))
dat_ref = ref.split("/")[-1].split("_")[-1].split(".")[0]

# Read -> Calculate ratio -> Write
file_list = sorted(glob.glob(os.path.join(modpath, '*.json')))
print(file_list)
for model in file_list:
    psdmfm_mod = json.load(open(model))
    mod = model.split("/")[-1].split("_")[-1].split(".")[0]
    ens = model.split("/")[-1].split("_")[-1].split(".")[1]
    dat_mod = mod + '.' + ens

    psdmfm = copy.deepcopy(psdmfm_mod)
    for frc in psdmfm_mod['RESULTS'][dat_mod].keys():
        for dom in psdmfm_mod['RESULTS'][dat_mod][frc].keys():
            for frq in psdmfm_mod['RESULTS'][dat_mod][frc][dom].keys():
                psdmfm['RESULTS'][dat_mod][frc][dom][frq] = psdmfm_mod['RESULTS'][dat_mod][frc][dom][frq] / \
                    psdmfm_ref['RESULTS'][dat_ref][frc][dom][frq]

    if not(os.path.isdir(outdir)):
        os.makedirs(outdir)
    outfile = open(os.path.join(outdir, model.split("/")[-1]), 'w')
    json.dump(psdmfm, outfile, sort_keys=True,
              indent=4, separators=(',', ': '))
    outfile.close()

    print('Complete ', dat_mod)
print('Complete all')
