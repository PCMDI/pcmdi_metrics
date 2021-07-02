import json
import glob
import copy
import os

# set path for ref and model
path = '/work/ahn6/pr/variability_across_timescales/power_spectrum/v20210123_test/metrics_results/precip_variability/'
ref = os.path.join(path, 'obs', 'v20210702',
                   'PS_pr.3hr_regrid.180x90_area.freq.mean_TRMM.json')
modpath = os.path.join(path, 'cmip6', 'historical', 'v20210702')

# Read reference data for ratio
psdmfm_ref = json.load(open(ref))
dat_ref = ref.split("/")[-1].split("_")[-1].split(".")[0]

# Read -> Calculate ratio -> Write
file_list = sorted(glob.glob(os.path.join(modpath, '*.json')))
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

    outdir = os.path.join(modpath, 'ratio')
    if not(os.path.isdir(outdir)):
        os.makedirs(outdir)
    outfile = open(os.path.join(outdir, model.split("/")[-1]), 'w')
    json.dump(psdmfm, outfile, sort_keys=True,
              indent=4, separators=(',', ': '))
    outfile.close()

    print('Complete ', dat_mod)
print('Complete all')
