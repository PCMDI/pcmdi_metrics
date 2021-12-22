#!/usr/bin/python
##########################################################################
# This code is based on below and modified for PMP
##########################################################################
# Python code to diagnose the unevenness of precipitation
# This script diagnoses the unevenness of precipitation according to the number of heaviest days of precipitation per year it takes to get half of total precipitation ([Pendergrass and Knutti 2018](https://doi.org/10.1029/2018GL080298)).
# Given one year of precip data, calculate the number of days for half of precipitation
# Ignore years with zero precip (by setting them to NaN).
##########################################################################
import os
import cdms2 as cdms
import MV2 as MV
import numpy as np
import glob
import copy
import pcmdi_metrics
from genutil import StringConstructor
from scipy.interpolate import interp1d
from pcmdi_metrics.driver.pmp_parser import PMPParser
# from pcmdi_metrics.precip_distribution.unevenness.lib import (
#     AddParserArgument,
#     Regrid,
#     getDailyCalendarMonth,
#     oneyear,
#     AvgDomain
# )
with open('../lib/argparse_functions.py') as source_file:
    exec(source_file.read())
with open('../lib/lib_dist_unevenness.py') as source_file:
    exec(source_file.read())

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
mip = param.mip
mod = param.mod
var = param.var
# dfrq = param.frq
modpath = param.modpath
prd = param.prd
fac = param.fac
res = param.res
nx_intp = int(360/res[0])
ny_intp = int(180/res[1])
print(modpath)
print(mod)
print(prd)
print(nx_intp, 'x', ny_intp)

# Get flag for CMEC output
cmec = param.cmec

missingthresh = 0.3  # threshold of missing data fraction at which a year is thrown out

# Create output directory
case_id = param.case_id
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(str(outdir_template(
    output_type='%(output_type)',
    mip=mip, case_id=case_id)))

for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        try:
            os.makedirs(outdir(output_type=output_type))
        except FileExistsError:
            pass
    print(outdir(output_type=output_type))

version = case_id

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

# Regridding -> Month separation -> Unevenness -> Domain average -> Write
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
        rgtmp = Regrid(do, res)
        if iyr == syr:
            drg = copy.deepcopy(rgtmp)
        else:
            drg = MV.concatenate((drg, rgtmp))
        print(iyr, drg.shape)

    # Month separation
    # months = ['ALL', 'JAN', 'FEB', 'MAR', 'APR', 'MAY',
    #           'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    months = ['ALL', 'JAN', 'FEB', 'MAR', 'APR', 'MAY',
              'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
              'MAM', 'JJA', 'SON', 'DJF']

    if "360" in cal:
        ndymon = [360, 30, 30, 30, 30, 30, 30, 30,
                  30, 30, 30, 30, 30, 90, 90, 90, 90]
    else:
        ndymon = [365, 31, 28, 31, 30, 31, 30, 31,
                  31, 30, 31, 30, 31, 92, 92, 91, 90]

    # Open nc file for writing data of spatial pattern of cumulated fractions with separated month
    outfilename = "dist_cumfrac_regrid." + \
        str(nx_intp)+"x"+str(ny_intp)+"_" + dat + ".nc"
    outcumfrac = cdms.open(os.path.join(
        outdir(output_type='diagnostic_results'), outfilename), "w")

    for im, mon in enumerate(months):

        if mon == 'ALL':
            dmon = drg
        elif mon == 'MAM':
            dmon = getDailyCalendarMonth(drg, ['MAR', 'APR', 'MAY'])
        elif mon == 'JJA':
            dmon = getDailyCalendarMonth(drg, ['JUN', 'JUL', 'AUG'])
        elif mon == 'SON':
            dmon = getDailyCalendarMonth(drg, ['SEP', 'OCT', 'NOV'])
        elif mon == 'DJF':
            # dmon = getDailyCalendarMonth(drg, ['DEC','JAN','FEB'])
            dmon = getDailyCalendarMonth(drg(
                time=(str(syr)+"-3-1 0:0:0", str(eyr)+"-11-30 23:59:59")), ['DEC', 'JAN', 'FEB'])
        else:
            dmon = getDailyCalendarMonth(drg, mon)

        print(dat, mon, dmon.shape)

        # Calculate unevenness
        nyr = eyr-syr+1
        if mon == 'DJF':
            nyr = nyr - 1
        cfy = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        prdyfracyr = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        sdiiyr = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        pfracyr = np.full(
            (nyr, ndymon[im], dmon.shape[1], dmon.shape[2]), np.nan)

        for iyr, year in enumerate(range(syr, eyr + 1)):
            if mon == 'DJF':
                if year == eyr:
                    thisyear = None
                else:
                    thisyear = dmon(time=(str(year) + "-12-1 0:0:0",
                                          str(year+1) + "-3-1 23:59:59"))
            else:
                thisyear = dmon(time=(str(year) + "-1-1 0:0:0",
                                      str(year) + "-12-" + str(ldy) + " 23:59:59"))

            if thisyear is not None:
                print(year, thisyear.shape)
                thisyear = thisyear.filled(np.nan)  # np.array(thisyear)
                pfrac, ndhy, prdyfrac, sdii = oneyear(thisyear, missingthresh)
                cfy[iyr, :, :] = ndhy
                prdyfracyr[iyr, :, :] = prdyfrac
                sdiiyr[iyr, :, :] = sdii
                pfracyr[iyr, :, :, :] = pfrac[:ndymon[im], :, :]
                print(year, 'pfrac.shape is ', pfrac.shape, ', but',
                      pfrac[:ndymon[im], :, :].shape, ' is used')

        ndm = np.nanmedian(cfy, axis=0)  # ignore years with zero precip
        missingfrac = (np.sum(np.isnan(cfy), axis=0)/nyr)
        ndm[np.where(missingfrac > missingthresh)] = np.nan
        prdyfracm = np.nanmedian(prdyfracyr, axis=0)
        sdiim = np.nanmedian(sdiiyr, axis=0)

        pfracm = np.nanmedian(pfracyr, axis=0)
        axbin = cdms.createAxis(range(1, ndymon[im]+1), id='cumday')
        lat = dmon.getLatitude()
        lon = dmon.getLongitude()
        pfracm = MV.array(pfracm)
        pfracm.setAxisList((axbin, lat, lon))
        outcumfrac.write(pfracm, id="cumfrac_"+mon)

    # Make Spatial pattern with separated months
        if im == 0:
            ndmmon = np.expand_dims(ndm, axis=0)
            prdyfracmmon = np.expand_dims(prdyfracm, axis=0)
            sdiimmon = np.expand_dims(sdiim, axis=0)
        else:
            ndmmon = MV.concatenate(
                (ndmmon, np.expand_dims(ndm, axis=0)), axis=0)
            prdyfracmmon = MV.concatenate(
                (prdyfracmmon, np.expand_dims(prdyfracm, axis=0)), axis=0)
            sdiimmon = MV.concatenate(
                (sdiimmon, np.expand_dims(sdiim, axis=0)), axis=0)

    # Domain average
    axmon = cdms.createAxis(range(len(months)), id='month')
    ndmmon = MV.array(ndmmon)
    ndmmon.setAxisList((axmon, lat, lon))
    prdyfracmmon = MV.array(prdyfracmmon)
    prdyfracmmon.setAxisList((axmon, lat, lon))
    sdiimmon = MV.array(sdiimmon)
    sdiimmon.setAxisList((axmon, lat, lon))
    metrics['RESULTS'][dat] = {}
    metrics['RESULTS'][dat]['unevenness'] = AvgDomain(ndmmon)
    metrics['RESULTS'][dat]['prdyfrac'] = AvgDomain(prdyfracmmon)
    metrics['RESULTS'][dat]['sdii'] = AvgDomain(sdiimmon)

    # Write data (nc file for spatial pattern of metrics)
    outfilename = "dist_cumfrac_unevenness_regrid." + \
        str(nx_intp)+"x"+str(ny_intp)+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(ndmmon, id="unevenness")
        out.write(prdyfracmmon, id="prdyfrac")
        out.write(sdiimmon, id="sdii")

    # Write data (json file for area averaged metrics)
    outfilename = "dist_cumfrac_unevenness_area.mean_regrid." + \
        str(nx_intp)+"x"+str(ny_intp)+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
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
