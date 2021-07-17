#!/usr/bin/python
##########################################################################
# This code is based on below and modified for PMP
##########################################################################
# Angeline Pendergrass, January 18 2017.
# Starting from precipitation data,
# 1. Calculate the distribution of rain
# 2. Plot the change from one climate state to another
# This code is ported from the matlab code shift-plus-increase-modes-demo, originally in matlab.
###
# You can read about these methods and cite the following papers about them:
# Pendergrass, A.G. and D.L. Hartmann, 2014: Two modes of change of the
# distribution of rain. Journal of Climate, 27, 8357-8371.
# doi:10.1175/JCLI-D-14-00182.1.
# and the shift and increase modes of response of the rainfall distribution
# to warming, occuring across ENSO events or global warming simulations.
# The response to warming is described in:
# Pendergrass, A.G. and D.L. Hartmann, 2014: Changes in the distribution
# of rain frequency and intensity in response to global warming.
# Journal of Climate, 27, 8372-8383. doi:10.1175/JCLI-D-14-00183.1.
###
# See github.com/apendergrass for the latest info and updates.
##########################################################################
import os
import sys
import cdms2 as cdms
import MV2 as MV
import numpy as np
import glob
import copy
import pcmdi_metrics
import cdutil
import collections
import datetime
from genutil import StringConstructor

# from pcmdi_metrics.driver.pmp_parser import PMPParser
# from pcmdi_metrics.precip_variability.lib import (
#     AddParserArgument,
#     Regrid2deg,
#     ClimAnom,
#     Powerspectrum,
#     Avg_PS_DomFrq,
# )
with open('./lib/argparse_functions.py') as source_file:
    exec(source_file.read())
with open('./lib/lib_dist_freq_amount_peak_width.py') as source_file:
    exec(source_file.read())

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

version = case_id

# It is daily average precipitation, in units of mm/d, with dimensions of lats, lons, and time.

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

# Regridding -> Month separation -> Distribution -> Domain average -> Metrics -> Write
metrics = {'RESULTS': {}}
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

    lat = drg.getLatitude()[:]
    lon = drg.getLongitude()[:]

    # Month separation
    months = ['ALL', 'JAN', 'FEB', 'MAR', 'APR', 'MAY',
              'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    amtpeakmap = np.empty((13, len(lat), len(lon)))
    amtwidthmap = np.empty((13, len(lat), len(lon)))
    pdfpeakmap = np.empty((13, len(lat), len(lon)))
    pdfwidthmap = np.empty((13, len(lat), len(lon)))
    for im, mon in enumerate(months):

        if mon == 'ALL':
            dmon = drg
        else
        dmon = getDailyCalendarMonth(drg, mon)

        print(dat, mon, dmon.shape)

        pdata1 = dmon

        # Calculate bin structure
        binl, binr, bincrates = CalcBinStructure(pdata1)

        # Calculate distributions
        ppdfmap, pamtmap = MakeDists(pdata1, binl)

        # Calculate the metrics for the distribution at each grid point
        for i in range(len(lon)):
            for j in range(len(lat)):
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pamtmap[j, i, :], bincrates)
                amtpeakmap[im, j, i] = rainpeak
                amtwidthmap[im, j, i] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    ppdfmap[j, i, :], bincrates)
                pdfpeakmap[im, j, i] = rainpeak
                pdfwidthmap[im, j, i] = rainwidth

    # Domain average
    metrics['RESULTS'][dat]['amtpeak'] = AvgDomain(amtpeakmap)
    metrics['RESULTS'][dat]['amtwidth'] = AvgDomain(amtwidthmap)
    metrics['RESULTS'][dat]['pdfpeak'] = AvgDomain(pdfpeakmap)
    metrics['RESULTS'][dat]['pdfwidth'] = AvgDomain(pdfwidthmap)

    # Write data (json file)
    outfilename = "dist_freq.amount_peak.width_regrid.180x90_area.mean_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(psdmfm,
               json_structure=["model+realization",
                               "metrics",
                               "domain"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))
