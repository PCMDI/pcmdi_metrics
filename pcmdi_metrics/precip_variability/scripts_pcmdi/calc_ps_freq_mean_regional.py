import datetime
import glob
import os
import pickle

import numpy as np
import xcdat as xc


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
# Which ensembles are included
# e.g. ['cmip6','obs']
mips = []
# Input directories. Only one domain/realization
# needs to be provided if there are multiple
model_root = ""
obs_root = ""
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

frcs = ["forced", "unforced"]
vars = ["power", "rednoise", "sig95"]

psfm = {}
for ifc, frc in enumerate(frcs):
    if frc == "forced":
        frqs = frqs_forced
    elif frc == "unforced":
        frqs = frqs_unforced

    psfm[frc] = {}
    for im, mip in enumerate(mips):
        if mip not in psfm[frc]:
            psfm[frc][mip] = {}
        if mip == "cmip6":
            root = model_root
        elif mip == "obs":
            root = obs_root
        if frc == "forced":
            file_list = sorted(
                set(glob.glob(os.path.join(root, "PS*")))
                - set(glob.glob(os.path.join(root, "PS*_unforced.nc")))
                - set(glob.glob(os.path.join(root, "PS*.json")))
            )
        elif frc == "unforced":
            file_list = sorted(set(glob.glob(os.path.join(root, "PS*_unforced.nc"))))

        f = []
        data = []
        for ifl in range(len(file_list)):
            file = file_list[ifl]
            if mip == "obs":
                tmp = file.split("/")[-1].split("_")[3]
                model = tmp.split(".")[0]
                data.append(model)
            else:
                tmp = file.split("/")[-1].split("_")[3]
                print(tmp)
                model = tmp.split(".")[0]
                ens = tmp.split(".")[1]
                data.append(model + "." + ens)
        print(mip, "# of data:", len(data))
        print(data)

        psfm[frc][mip] = {}
        for id, dat in enumerate(data):
            ds = xc.open_dataset(file_list[id])
            frequency = ds["freqs"]

            psfm[frc][mip][dat] = {}
            for iv, var in enumerate(vars):
                print(frc, mip, dat, var)
                power = ds[var]

                psfm[frc][mip][dat][var] = {}
                for frq in frqs:
                    if frq == "semi-diurnal":  # pr=0.5day
                        idx = prdday_to_frqidx(0.5, frequency, ntd)
                        fm = power.isel({"frequency": idx}).data
                    elif frq == "diurnal":  # pr=1day
                        idx = prdday_to_frqidx(1, frequency, ntd)
                        fm = power.isel({"frequency": idx}).data
                    if frq == "semi-annual":  # 180day=<pr=<183day
                        idx2 = prdday_to_frqidx(180, frequency, ntd)
                        idx1 = prdday_to_frqidx(183, frequency, ntd)
                        fm = (
                            power.isel({"frequency": slice(idx1, idx2 + 1)})
                            .max("frequency")
                            .data
                        )
                    elif frq == "annual":  # 360day=<pr=<366day
                        idx2 = prdday_to_frqidx(360, frequency, ntd)
                        idx1 = prdday_to_frqidx(366, frequency, ntd)
                        fm = (
                            power.isel({"frequency": slice(idx1, idx2 + 1)})
                            .max("frequency")
                            .data
                        )
                    elif frq == "sub-daily":  # pr<1day
                        idx1 = prdday_to_frqidx(1, frequency, ntd)
                        fm = (
                            power.isel(
                                {"frequency": slice(idx1 + 1, len(frequency) - 1)}
                            )
                            .mean("frequency")
                            .data
                        )
                    elif frq == "synoptic":  # 1day=<pr<20day
                        idx2 = prdday_to_frqidx(1, frequency, ntd)
                        idx1 = prdday_to_frqidx(20, frequency, ntd)
                        fm = (
                            power.isel({"frequency": slice(idx1 + 1, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "sub-seasonal":  # 20day=<pr<90day
                        idx2 = prdday_to_frqidx(20, frequency, ntd)
                        idx1 = prdday_to_frqidx(90, frequency, ntd)
                        fm = (
                            power.isel({"frequency": slice(idx1 + 1, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "seasonal-annual":  # 90day=<pr<365day
                        idx2 = prdday_to_frqidx(90, frequency, ntd)
                        idx1 = prdday_to_frqidx(365, frequency, ntd)
                        fm = (
                            power.isel({"frequency": slice(idx1 + 1, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "interannual":  # 365day=<pr
                        idx2 = prdday_to_frqidx(365, frequency, ntd)
                        fm = (
                            power.isel({"frequency": slice(0, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )

                    psfm[frc][mip][dat][var][frq] = fm.tolist()
            ds.close()

res = os.path.basename(file_list[0]).split("_")[2].split(".")[1]

outdir = os.path.join(outdir, ver)  # add version to outdir
if not (os.path.isdir(outdir)):
    os.makedirs(outdir)
outfile = open(
    os.path.join(outdir, "PS_pr.{0}_regrid.{1}_freq.mean.pkl".format(hr, res)), "wb"
)
pickle.dump(psfm, outfile)
outfile.close()
