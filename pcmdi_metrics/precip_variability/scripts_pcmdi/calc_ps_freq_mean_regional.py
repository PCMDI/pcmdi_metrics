import datetime
import glob
import os
import pickle

import numpy as np
import xcdat as xc


def prdday_to_frq3hridx(prdday, frequency):
    frq3hr = 1.0 / (float(prdday) * 8.0)
    idx = (np.abs(frequency - frq3hr)).argmin()
    return int(idx)


def prdday_to_frq1didx(prdday, frequency):
    frq24hr = 1.0 / (float(prdday))
    idx = (np.abs(frequency - frq24hr)).argmin()
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
elif hr == "3hr":
    frqs_forced = ["semi-diurnal", "diurnal", "semi-annual", "annual"]
    frqs_unforced = [
        "sub-daily",
        "synoptic",
        "sub-seasonal",
        "seasonal-annual",
        "interannual",
    ]

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
                        idx = prdday_to_frq3hridx(0.5, frequency)
                        fm = power.isel({"frequency": idx}).data
                    elif frq == "diurnal":  # pr=1day
                        idx = prdday_to_frq3hridx(1, frequency)
                        fm = power.isel({"frequency": idx}).data
                    if frq == "semi-annual":  # 180day=<pr=<183day
                        if hr == "day":
                            idx2 = prdday_to_frq1didx(180, frequency)
                            idx1 = prdday_to_frq1didx(183, frequency)
                        elif hr == "3hr":
                            idx2 = prdday_to_frq3hridx(180, frequency)
                            idx1 = prdday_to_frq3hridx(183, frequency)
                        fm = (
                            power.isel({"frequency": slice(idx1, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "annual":  # 360day=<pr=<366day
                        if hr == "day":
                            idx2 = prdday_to_frq1didx(360, frequency)
                            idx1 = prdday_to_frq1didx(366, frequency)
                        elif hr == "3hr":
                            idx2 = prdday_to_frq3hridx(360, frequency)
                            idx1 = prdday_to_frq3hridx(366, frequency)
                        fm = (
                            power.isel({"frequency": slice(idx1, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "sub-daily":  # pr<1day
                        idx1 = prdday_to_frq1didx(1, frequency)
                        fm = (
                            power.isel({"frequency": slice(0, idx1 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "synoptic":  # 1day=<pr<20day
                        if hr == "day":
                            idx2 = prdday_to_frq1didx(1, frequency)
                            idx1 = prdday_to_frq1didx(20, frequency)
                        elif hr == "3hr":
                            idx2 = prdday_to_frq3hridx(1, frequency)
                            idx1 = prdday_to_frq3hridx(20, frequency)
                        fm = (
                            power.isel({"frequency": slice(idx1 + 1, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "sub-seasonal":  # 20day=<pr<90day
                        if hr == "day":
                            idx2 = prdday_to_frq1didx(20, frequency)
                            idx1 = prdday_to_frq1didx(90, frequency)
                        elif hr == "3hr":
                            idx2 = prdday_to_frq3hridx(20, frequency)
                            idx1 = prdday_to_frq3hridx(90, frequency)
                        fm = (
                            power.isel({"frequency": slice(idx1 + 1, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "seasonal-annual":  # 90day=<pr<365day
                        if hr == "day":
                            idx2 = prdday_to_frq1didx(90, frequency)
                            idx1 = prdday_to_frq1didx(365, frequency)
                        elif hr == "3hr":
                            idx2 = prdday_to_frq3hridx(90, frequency)
                            idx1 = prdday_to_frq3hridx(365, frequency)
                        fm = (
                            power.isel({"frequency": slice(idx1 + 1, idx2 + 1)})
                            .mean("frequency")
                            .data
                        )
                    elif frq == "interannual":  # 365day=<pr
                        if hr == "day":
                            idx2 = prdday_to_frq1didx(365, frequency)
                        elif hr == "3hr":
                            idx2 = prdday_to_frq1didx(365, frequency)
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
