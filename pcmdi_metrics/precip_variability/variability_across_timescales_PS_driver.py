import cdms2 as cdms
import MV2 as MV
import glob
import copy
import os
import sys
import pcmdi_metrics
from genutil import StringConstructor
from pcmdi_metrics.driver.pmp_parser import PMPParser
from pcmdi_metrics.precip_variability.lib import (
    AddParserArgument,
    Regrid2deg,
    ClimAnom,
    Powerspectrum,
    Avg_PS_DomFrq,
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
outdir = StringConstructor(str(outdir_template(
    output_type='%(output_type)',
    mip=mip, case_id=case_id)))
for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        os.makedirs(outdir(output_type=output_type))
    print(outdir(output_type=output_type))

# Read data
file_list = sorted(glob.glob(os.path.join(modpath, "*" + mod + "*")))
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

# Regridding -> Anomaly -> Power spectra -> Domain&Frequency average -> Write
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
    elif dfrq == "3hr":
        ntd = 8
    else:
        sys.exit("ERROR: dfrq "+dfrq+" is not defined!")
    clim, anom = ClimAnom(drg, ntd, syr, eyr)

    # Power spectum of total
    freqs, ps, rn, sig95 = Powerspectrum(drg, nperseg, noverlap)
    # Domain & Frequency average
    psdmfm_forced = Avg_PS_DomFrq(ps, freqs, ntd, dat, mip, 'forced')
    # Write data (nc file)
    outfilename = "PS_pr." + str(dfrq) + "_regrid.180x90_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(freqs, id="freqs")
        out.write(ps, id="power")
        out.write(rn, id="rednoise")
        out.write(sig95, id="sig95")

    # Power spectum of anomaly
    freqs, ps, rn, sig95 = Powerspectrum(anom, nperseg, noverlap)
    # Domain & Frequency average
    psdmfm_unforced = Avg_PS_DomFrq(ps, freqs, ntd, dat, mip, 'unforced')
    # Write data (nc file)
    outfilename = "PS_pr." + \
        str(dfrq) + "_regrid.180x90_" + dat + "_unforced.nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(freqs, id="freqs")
        out.write(ps, id="power")
        out.write(rn, id="rednoise")
        out.write(sig95, id="sig95")

    # Write data (json file)
    psdmfm = {'RESULTS': {}}
    psdmfm['RESULTS'][dat] = {}
    psdmfm['RESULTS'][dat]['forced'] = psdmfm_forced
    psdmfm['RESULTS'][dat]['unforced'] = psdmfm_unforced

    outfilename = "PS_pr." + \
        str(dfrq) + "_regrid.180x90_area.freq.mean_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(psdmfm,
               json_structure=["model+realization",
                               "variability type",
                               "domain",
                               "frequency"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))
