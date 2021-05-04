import cdms2 as cdms
import MV2 as MV
import glob
import copy
import os
from pcmdi_metrics.pcmdi.pmp_parser import PMPParser
from pcmdi_metrics.precip_variability.lib import (
    AddParserArgument,
    Regrid2deg,
    ClimAnom,
    Powerspectrum,
    StandardDeviation,
)

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
args = P.get_parameter()
mip = args.mip
mod = args.mod
var = args.var
dfrq = args.frq
modpath = args.modpath
outdir = args.outdir
prd = args.prd
fac = args.fac
nperseg = args.nperseg
noverlap = args.noverlap
print(modpath)
print(mod)
print(prd)
print(nperseg, noverlap)

# Read data
file_list = sorted(glob.glob(modpath + "*" + mod + "*"))
f = []
data = []
for ifl in range(len(file_list)):
    f.append(cdms.open(file_list[ifl]))
    file = file_list[ifl]
    if mip == "obs":
        model = file.split("/")[-1].split(".")[2]
        data.append(model)
    else:
        model = file.split("/")[-1].split(".")[2]
        ens = file.split("/")[-1].split(".")[3]
        data.append(model + "." + ens)
print("# of data:", len(data))
print(data)

# Make output directory
if not (os.path.isdir(outdir)):
    os.makedirs(outdir)

# Regridding -> Anomaly -> Power spectra -> Write
syr = prd[0]
eyr = prd[1]
for id, dat in enumerate(data):
    cal = f[id][var].getTime().calendar
    if "360" in cal:
        ldy = 30
    else:
        ldy = 31
    print(dat, cal)
    for iyr in range(syr, eyr + 1):
        do = (
            f[id](
                var,
                time=(
                    str(iyr) + "-1-1 0:0:0",
                    str(iyr) + "-12-" + str(ldy) + " 23:59:59",
                ),
            ) * float(fac)
        )

        # Regridding
        rgtmp = Regrid2deg(do)
        if iyr == syr:
            drg = copy.deepcopy(rgtmp)
        else:
            drg = MV.concatenate((drg, rgtmp))
        print(iyr, drg.shape)

    # Anomaly
    if dfrq == "day":
        ntd = 1
    if dfrq == "3hr":
        ntd = 8
    clim, anom = ClimAnom(drg, ntd, syr, eyr)

    # Power spectum of total
    freqs, ps, rn, sig95 = Powerspectrum(drg, nperseg, noverlap)
    # Write data (nc file)
    freqs = MV.array(freqs)
    ps = MV.array(ps)
    rn = MV.array(rn)
    sig95 = MV.array(sig95)
    frq = cdms.createAxis(range(len(freqs)), id="frequency")
    lat = drg.getLatitude()
    lon = drg.getLongitude()
    freqs.setAxis(0, frq)
    ps.setAxisList((frq, lat, lon))
    rn.setAxisList((frq, lat, lon))
    sig95.setAxisList((frq, lat, lon))
    out = cdms.open(
        outdir + "PS_pr." + str(dfrq) + "_regrid.180x90_" + dat + ".nc", "w"
    )
    out.write(freqs, id="freqs")
    out.write(ps, id="power")
    out.write(rn, id="rednoise")
    out.write(sig95, id="sig95")
    out.close()

    # Power spectum of anomaly
    freqs, ps, rn, sig95 = Powerspectrum(anom, nperseg, noverlap)
    # Write data (nc file)
    freqs = MV.array(freqs)
    ps = MV.array(ps)
    rn = MV.array(rn)
    sig95 = MV.array(sig95)
    frq = cdms.createAxis(range(len(freqs)), id="frequency")
    lat = drg.getLatitude()
    lon = drg.getLongitude()
    freqs.setAxis(0, frq)
    ps.setAxisList((frq, lat, lon))
    rn.setAxisList((frq, lat, lon))
    sig95.setAxisList((frq, lat, lon))
    out = cdms.open(
        outdir + "PS_pr." + str(dfrq) + "_regrid.180x90_" +
        dat + "_unforced.nc", "w"
    )
    out.write(freqs, id="freqs")
    out.write(ps, id="power")
    out.write(rn, id="rednoise")
    out.write(sig95, id="sig95")
    out.close()

    # STD of total
    std = StandardDeviation(drg, 0)
    # Write data (nc file)
    std = MV.array(std)
    lat = drg.getLatitude()
    lon = drg.getLongitude()
    std.setAxisList((lat, lon))
    out = cdms.open(
        outdir + "STD_pr." + str(dfrq) + "_regrid.180x90_" + dat + ".nc", "w"
    )
    out.write(std, id="std")
    out.close()

    # STD of anomaly
    std = StandardDeviation(anom, 0)
    # Write data (nc file)
    std = MV.array(std)
    lat = drg.getLatitude()
    lon = drg.getLongitude()
    std.setAxisList((lat, lon))
    out = cdms.open(
        outdir + "STD_pr." + str(dfrq) + "_regrid.180x90_" +
        dat + "_unforced.nc", "w"
    )
    out.write(std, id="std")
    out.close()
