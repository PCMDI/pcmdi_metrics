import copy
import datetime
import json
import os
import pickle

import numpy as np


def prdday_to_frqidx(prdday, frequency, ntd):
    """
    Find frequency index from input period
    Input
    - prdday: period (day)
    - frequency: frequency
    - ntd: number of time steps per day (daily: 1, 3-hourly: 8)
    Output
    - idx: frequency index
    """
    frq = 1.0 / (float(prdday) * ntd)
    idx = (np.abs(frequency - frq)).argmin()
    return int(idx)


# --------------------
# User settings here
# --------------------
# "3hr" or "day"
hr = ""
# Input file name (pickle .pkl output from calc_ps_area.mean.py)
fname = ""
# Output directory (not including version)
outdir = ""

# -----------------------
# The rest of the script
# -----------------------
ver = datetime.datetime.now().strftime("v%Y%m%d")

if hr == "day":
    frqs_forced = ["semi-annual", "annual"]
    frqs_unforced = ["synoptic", "sub-seasonal", "seasonal-annual", "interannual"]
    ntd = 1
elif hr == "3hr":
    frqs_forced = ["semi-diurnal", "diurnal", "semi-annual", "annual"]
    frqs_unforced = [
        "sub-daily",
        "synoptic",
        "sub-seasonal",
        "seasonal-annual",
        "interannual",
    ]
    ntd = 8

infile = open(fname, "rb")
psdm = pickle.load(infile)

psdmfm = copy.deepcopy(psdm)
for frc in psdm.keys():
    if frc == "forced":
        frqs = frqs_forced
    elif frc == "unforced":
        frqs = frqs_unforced
    print(frc)
    for mip in psdm[frc].keys():
        print(mip)
        for dat in psdm[frc][mip].keys():
            frequency = np.array(psdm[frc][mip][dat]["freqs"])
            del psdm[frc][mip][dat]["freqs"]
            del psdmfm[frc][mip][dat]["freqs"]

            for var in psdm[frc][mip][dat].keys():
                print(dat, var)
                for idm, dom in enumerate(psdm[frc][mip][dat][var].keys()):
                    am = np.array(psdm[frc][mip][dat][var][dom])
                    del psdmfm[frc][mip][dat][var][dom]
                    psdmfm[frc][mip][dat][var][dom] = {}
                    print(dom)
                    for frq in frqs:
                        print(frq)
                        if frq == "semi-diurnal":  # pr=0.5day
                            idx = prdday_to_frqidx(0.5, frequency, ntd)
                            amfm = am[idx]
                        elif frq == "diurnal":  # pr=1day
                            idx = prdday_to_frqidx(1, frequency, ntd)
                            amfm = am[idx]
                        if frq == "semi-annual":  # 180day=<pr=<183day
                            idx2 = prdday_to_frqidx(180, frequency, ntd)
                            idx1 = prdday_to_frqidx(183, frequency, ntd)
                            amfm = np.amax(am[idx1 : idx2 + 1])
                        elif frq == "annual":  # 360day=<pr=<366day
                            idx2 = prdday_to_frqidx(360, frequency, ntd)
                            idx1 = prdday_to_frqidx(366, frequency, ntd)
                            amfm = np.amax(am[idx1 : idx2 + 1])
                        elif frq == "sub-daily":  # pr<1day
                            idx1 = prdday_to_frqidx(1, frequency, ntd)
                            amfm = np.nanmean(am[idx1 + 1 :])
                        elif frq == "synoptic":  # 1day=<pr<20day
                            idx2 = prdday_to_frqidx(1, frequency, ntd)
                            idx1 = prdday_to_frqidx(20, frequency, ntd)
                            amfm = np.nanmean(am[idx1 + 1 : idx2 + 1])
                        elif frq == "sub-seasonal":  # 20day=<pr<90day
                            idx2 = prdday_to_frqidx(20, frequency, ntd)
                            idx1 = prdday_to_frqidx(90, frequency, ntd)
                            amfm = np.nanmean(am[idx1 + 1 : idx2 + 1])
                        elif frq == "seasonal-annual":  # 90day=<pr<365day
                            idx2 = prdday_to_frqidx(90, frequency, ntd)
                            idx1 = prdday_to_frqidx(365, frequency, ntd)
                            amfm = np.nanmean(am[idx1 + 1 : idx2 + 1])
                        elif frq == "interannual":  # 365day=<pr
                            idx2 = prdday_to_frqidx(365, frequency, ntd)
                            amfm = np.nanmean(am[: idx2 + 1])

                        psdmfm[frc][mip][dat][var][dom][frq] = amfm.tolist()

res = os.path.basename(fname).split("_")[2].split(".")[1]

outdir = os.path.join(outdir, ver)  # add version to outdir
if not (os.path.isdir(outdir)):
    os.makedirs(outdir)

# Save as pickle for figure creation
outfile = open(
    outdir + "/PS_pr.{0}_regrid.{1}_area.freq.mean.forced.pkl".format(hr, res), "wb"
)
pickle.dump(psdmfm, outfile)
outfile.close()

# Write to JSON file
outfile = open(
    outdir + "/PS_pr.{0}_regrid.{1}_area.freq.mean.forced.json".format(hr, res), "w"
)
json.dump(psdmfm, outfile, sort_keys=True, indent=4, separators=(",", ": "))
outfile.close()
