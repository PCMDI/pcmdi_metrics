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
import cdms2 as cdms
import MV2 as MV
import numpy as np
import glob
import copy
import pcmdi_metrics
from genutil import StringConstructor
from pcmdi_metrics.driver.pmp_parser import PMPParser
# from pcmdi_metrics.precip_distribution.frequency_amount_peak.lib import (
#     AddParserArgument,
#     Regrid,
#     getDailyCalendarMonth,
#     CalcBinStructure,
#     MakeDists,
#     CalcRainMetrics,
#     AvgDomain
# )
with open('../lib/argparse_functions.py') as source_file:
    exec(source_file.read())
with open('../lib/lib_dist_freq_amount_peak_width.py') as source_file:
    exec(source_file.read())

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
mip = param.mip
mod = param.mod
var = param.var
modpath = param.modpath
ref = param.ref
prd = param.prd
fac = param.fac
res = param.res
res_nxny=str(int(360/res[0]))+"x"+str(int(180/res[1]))
print(modpath)
print(mod)
print(prd)
print(res_nxny)
print('Ref:', ref)

# Get flag for CMEC output
cmec = param.cmec

# Create output directory
case_id = param.case_id
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(str(outdir_template(
    output_type='%(output_type)', mip=mip, case_id=case_id)))

refdir_template = param.process_templated_argument("ref_dir")
refdir = StringConstructor(str(refdir_template(
    output_type='%(output_type)', case_id=case_id)))
refdir = refdir(output_type='diagnostic_results')

for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        try:
            os.makedirs(outdir(output_type=output_type))
        except FileExistsError:
            pass
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
        # model = file.split("/")[-1].split(".")[4]
        ens = file.split("/")[-1].split(".")[3]
        # ens = file.split("/")[-1].split(".")[5]
        data.append(model + "." + ens)
print("# of data:", len(data))
print(data)

# Regridding -> Month separation -> Distribution -> Metrics -> Domain average -> Write
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
    months = ['ANN', 'MAM', 'JJA', 'SON', 'DJF', 
              'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    pdfpeakmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    pdfwidthmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    amtpeakmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    amtwidthmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    for im, mon in enumerate(months):

        if mon == 'ANN':
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

        pdata1 = dmon

        # Calculate bin structure
        binl, binr, bincrates = CalcBinStructure(pdata1)

        # Calculate distributions at each grid point
        ppdfmap, pamtmap, bins, ppdfmap_tn = MakeDists(pdata1, binl)
        
        # Calculate metrics from the distribution at each grid point
        for i in range(drg.shape[2]):
            for j in range(drg.shape[1]):
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    ppdfmap[:, j, i], bincrates)
                pdfpeakmap[im, j, i] = rainpeak
                pdfwidthmap[im, j, i] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pamtmap[:, j, i], bincrates)
                amtpeakmap[im, j, i] = rainpeak
                amtwidthmap[im, j, i] = rainwidth

    # Make Spatial pattern of distributions with separated months
        if im == 0:
            pdfmapmon = np.expand_dims(ppdfmap, axis=0)
            pdfmapmon_tn = np.expand_dims(ppdfmap_tn, axis=0)
            amtmapmon = np.expand_dims(pamtmap, axis=0)
        else:
            pdfmapmon = MV.concatenate(
                (pdfmapmon, np.expand_dims(ppdfmap, axis=0)), axis=0)
            pdfmapmon_tn = MV.concatenate(
                (pdfmapmon_tn, np.expand_dims(ppdfmap_tn, axis=0)), axis=0)
            amtmapmon = MV.concatenate(
                (amtmapmon, np.expand_dims(pamtmap, axis=0)), axis=0)

    axmon = cdms.createAxis(range(len(months)), id='month')
    axbin = cdms.createAxis(range(len(binl)), id='bin')
    lat = drg.getLatitude()
    lon = drg.getLongitude()
    pdfmapmon.setAxisList((axmon, axbin, lat, lon))
    pdfmapmon_tn.setAxisList((axmon, axbin, lat, lon))
    amtmapmon.setAxisList((axmon, axbin, lat, lon))
    
    # Domain average of metrics
    pdfpeakmap = MV.array(pdfpeakmap)
    pdfwidthmap = MV.array(pdfwidthmap)
    amtpeakmap = MV.array(amtpeakmap)
    amtwidthmap = MV.array(amtwidthmap)
    pdfpeakmap.setAxisList((axmon, lat, lon))
    pdfwidthmap.setAxisList((axmon, lat, lon))
    amtpeakmap.setAxisList((axmon, lat, lon))
    amtwidthmap.setAxisList((axmon, lat, lon))
    metrics['RESULTS'][dat] = {}
    metrics['RESULTS'][dat]['frqpeak'] = AvgDomain(pdfpeakmap)
    metrics['RESULTS'][dat]['frqwidth'] = AvgDomain(pdfwidthmap)
    metrics['RESULTS'][dat]['amtpeak'] = AvgDomain(amtpeakmap)
    metrics['RESULTS'][dat]['amtwidth'] = AvgDomain(amtwidthmap)

    # Write data (nc file for spatial pattern of distributions)
    outfilename = "dist_freq.amount_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfmapmon, id="pdf")
        out.write(pdfmapmon_tn, id="pdf_tn")
        out.write(amtmapmon, id="amt")
        out.write(bins, id="binbounds")

    # Write data (nc file for spatial pattern of metrics)
    outfilename = "dist_freq.amount_peak.width_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfpeakmap, id="frqpeak")
        out.write(pdfwidthmap, id="frqwidth")
        out.write(amtpeakmap, id="amtpeak")
        out.write(amtwidthmap, id="amtwidth")

    # Write data (json file for area averaged metrics)
    outfilename = "dist_freq.amount_peak.width_area.mean_regrid." + \
        res_nxny+"_" + dat + ".json"
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
    
    
    
    # Domain averaged distribution -> Metrics -> Write    
    # Calculate metrics from the distribution at each domain        
    metricsdom = {'RESULTS': {dat: {}}}
    metricsdom3C = {'RESULTS': {dat: {}}}
    metricsdomAR6 = {'RESULTS': {dat: {}}}
    metricsdom['RESULTS'][dat], pdfdom, amtdom = CalcMetricsDomain(pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir)
    metricsdom3C['RESULTS'][dat], pdfdom3C, amtdom3C = CalcMetricsDomain3Clust(pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir)
    metricsdomAR6['RESULTS'][dat], pdfdomAR6, amtdomAR6 = CalcMetricsDomainAR6(pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir)

    # Write data (nc file for distributions at each domain)
    outfilename = "dist_freq.amount_domain_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfdom, id="pdf")
        out.write(amtdom, id="amt")
        out.write(bins, id="binbounds")
        
    # Write data (nc file for distributions at each domain with 3 clustering regions)
    outfilename = "dist_freq.amount_domain3C_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfdom3C, id="pdf")
        out.write(amtdom3C, id="amt")
        out.write(bins, id="binbounds")
    
    # Write data (nc file for distributions at each domain with AR6 regions)
    outfilename = "dist_freq.amount_domainAR6_regrid." + \
        res_nxny+"_" + dat + ".nc"
    with cdms.open(os.path.join(outdir(output_type='diagnostic_results'), outfilename), "w") as out:
        out.write(pdfdomAR6, id="pdf")
        out.write(amtdomAR6, id="amt")
        out.write(bins, id="binbounds")
    
 
    # Write data (json file for domain metrics)
    outfilename = "dist_freq.amount_peak.width_domain_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metricsdom,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))

    # Write data (json file for domain metrics with 3 clustering regions)
    outfilename = "dist_freq.amount_peak.width_domain3C_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metricsdom3C,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))
        
    # Write data (json file for domain metrics with AR6 regions)
    outfilename = "dist_freq.amount_peak.width_domainAR6_regrid." + \
        res_nxny+"_" + dat + ".json"
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'), outfilename)
    JSON.write(metricsdomAR6,
               json_structure=["model+realization",
                               "metrics",
                               "domain",
                               "month"],
               sort_keys=True,
               indent=4,
               separators=(',', ': '))
    if cmec:
        JSON.write_cmec(indent=4, separators=(',', ': '))
        