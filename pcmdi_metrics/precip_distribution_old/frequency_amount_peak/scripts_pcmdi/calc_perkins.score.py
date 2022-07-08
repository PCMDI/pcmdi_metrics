import cdms2 as cdms
import MV2 as MV
import numpy as np
import pcmdi_metrics
import glob
import os
from pcmdi_metrics.driver.pmp_parser import PMPParser
with open('../lib/argparse_functions.py') as source_file:
    exec(source_file.read())
with open('../lib/lib_dist_freq_amount_peak_width.py') as source_file:
    exec(source_file.read())

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
exp = param.exp
ref = param.ref
res = param.resn
ver = param.ver
inpath = param.modpath
outpath = param.results_dir
var = 'pdf'
print('reference: ', ref)
print('exp: ', exp)
print('resolution: ', res)
print('inpath: ', inpath)
print('outpath: ', outpath)

# Get flag for CMEC output
cmec = param.cmec


# metric_list = ['dist_freq.amount_regrid.', 'dist_freq.amount_domain_regrid.', 'dist_freq.amount_domain3C_regrid.', 'dist_freq.amount_domainAR6_regrid.']
metric_list = ['dist_freq.amount_domain_regrid.', 'dist_freq.amount_domain3C_regrid.', 'dist_freq.amount_domainAR6_regrid.']

for met in metric_list:

    # Read reference data
    file_ref = os.path.join(inpath, 'obs', ver, met+res+'_'+ref+'.nc')
    dist_ref = cdms.open(file_ref)[var]
    
    file_list1 = sorted(glob.glob(os.path.join(inpath, 'obs', ver, met+res+'_*.nc')))
    file_list2 = sorted(glob.glob(os.path.join(inpath, '*', exp, ver, met+res+'_*.nc')))
    file_list = file_list1 + file_list2
    
    print('Data name')
    print(met)
    print('Reference file')
    print(file_ref)
    print('Model files')
    print(file_list)
        
    if met == 'dist_freq.amount_regrid.':
        outfile_map = "dist_freq_pscore_regrid."
        outfile_metric = "dist_freq_pscore_area.mean_regrid."
        
        # Read -> Calculate Perkins score -> Domain average -> Write
        for model in file_list:
            metrics = {'RESULTS': {}}

            dist_mod = cdms.open(model)[var]
            mip = model.split("/")[9]
            if mip == 'obs':
                mod = model.split("/")[-1].split("_")[-1].split(".")[0]
                dat = mod
            else:
                mod = model.split("/")[-1].split("_")[-1].split(".")[0]
                ens = model.split("/")[-1].split("_")[-1].split(".")[1]
                dat = mod + '.' + ens

            perkins_score = np.sum(np.minimum(dist_ref, dist_mod), axis=1)
            perkins_score = MV.array(perkins_score)
            perkins_score.setAxisList(
                (dist_ref.getAxis(0), dist_ref.getAxis(2), dist_ref.getAxis(3)))

            metrics['RESULTS'][dat] = {}
            metrics['RESULTS'][dat]['pscore'] = AvgDomain(perkins_score)

            # Write data (nc file for spatial pattern of Perkins score)
            if mip == 'obs':
                outdir = os.path.join(outpath, 'diagnostic_results',
                                      'precip_distribution', mip, ver)
            else:
                outdir = os.path.join(outpath, 'diagnostic_results',
                                      'precip_distribution', mip, exp, ver)
            outfilename = outfile_map+res+"_" + dat + ".nc"
            with cdms.open(os.path.join(outdir, outfilename), "w") as out:
                out.write(perkins_score, id="pscore")

            # Write data (json file for area averaged metrics)
            if mip == 'obs':
                outdir = os.path.join(outpath, 'metrics_results',
                                      'precip_distribution', mip, ver)
            else:
                outdir = os.path.join(
                    outpath, 'metrics_results', 'precip_distribution', mip, exp, ver)
            outfilename = outfile_metric+res+"_" + dat + ".json"
            JSON = pcmdi_metrics.io.base.Base(outdir, outfilename)
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

            print('Complete ', met, mip, dat)
        
    else:
                    
        if met == 'dist_freq.amount_domain_regrid.':
            outfile_map = "dist_freq_pscore_domain_regrid."
            outfile_metric = "dist_freq_pscore_domain_regrid."
            domains = ["Total_50S50N", "Ocean_50S50N", "Land_50S50N",
                       "Total_30N50N", "Ocean_30N50N", "Land_30N50N",
                       "Total_30S30N", "Ocean_30S30N", "Land_30S30N",
                       "Total_50S30S", "Ocean_50S30S", "Land_50S30S"]
        elif met == 'dist_freq.amount_domain3C_regrid.':
            outfile_map = "dist_freq_pscore_domain3C_regrid."
            outfile_metric = "dist_freq_pscore_domain3C_regrid."
            domains = ["HR_50S50N", "MR_50S50N", "LR_50S50N",
                       "HR_30N50N", "MR_30N50N", "LR_30N50N",
                       "HR_30S30N", "MR_30S30N", "LR_30S30N",
                       "HR_50S30S", "MR_50S30S", "LR_50S30S"] 
        elif met == 'dist_freq.amount_domainAR6_regrid.':
            outfile_map = "dist_freq_pscore_domainAR6_regrid."
            outfile_metric = "dist_freq_pscore_domainAR6_regrid."
            ar6_land = regionmask.defined_regions.ar6.land            
            land_abbrevs = ar6_land.abbrevs            
            ocean_abbrevs = [ 'ARO', 
                              'ARS', 'BOB', 'EIO', 'SIO', 
                              'NPO', 'NWPO', 'NEPO', 'PITCZ',
                              'SWPO', 'SEPO', 'NAO', 'NEAO', 
                              'AITCZ', 'SAO', 'SOO', 
                            ]
            abbrevs = land_abbrevs + ocean_abbrevs
            domains = abbrevs
        else:
            print('ERROR: No domain information')
            exit()
        
        months = ['ANN', 'MAM', 'JJA', 'SON', 'DJF', 
                  'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                  'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # Read domain averaged pdf -> Calculate Perkins score -> Write
        for model in file_list:
            metrics = {'RESULTS': {}}

            dist_mod = cdms.open(model)[var]
            mip = model.split("/")[9]
            if mip == 'obs':
                mod = model.split("/")[-1].split("_")[-1].split(".")[0]
                dat = mod
            else:
                mod = model.split("/")[-1].split("_")[-1].split(".")[0]
                ens = model.split("/")[-1].split("_")[-1].split(".")[1]
                dat = mod + '.' + ens

            # perkins_score = np.sum(np.minimum(dist_ref, dist_mod), axis=1)
            perkins_score = np.sum(np.minimum(dist_ref, dist_mod), axis=2)
            perkins_score = MV.array(perkins_score)
            # perkins_score.setAxisList((dist_ref.getAxis(0), dist_ref.getAxis(2), dist_ref.getAxis(3)))
            perkins_score.setAxisList((dist_ref.getAxis(0), dist_ref.getAxis(1)))

            metrics['RESULTS'][dat] = {'pscore': {}}
            for idm, dom in enumerate(domains):
                metrics['RESULTS'][dat]['pscore'][dom] = {'CalendarMonths':{}}
                for im, mon in enumerate(months):
                    if mon in ['ANN', 'MAM', 'JJA', 'SON', 'DJF']:            
                        metrics['RESULTS'][dat]['pscore'][dom][mon] = perkins_score.tolist()[idm][im]
                    else:
                        calmon=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
                        imn=calmon.index(mon)+1
                        metrics['RESULTS'][dat]['pscore'][dom]['CalendarMonths'][imn] = perkins_score.tolist()[idm][im]

            # Write data (nc file for spatial pattern of Perkins score)
            if mip == 'obs':
                outdir = os.path.join(outpath, 'diagnostic_results',
                                      'precip_distribution', mip, ver)
            else:
                outdir = os.path.join(outpath, 'diagnostic_results',
                                      'precip_distribution', mip, exp, ver)            
            outfilename = outfile_map+res+"_" + dat + ".nc"            
            with cdms.open(os.path.join(outdir, outfilename), "w") as out:
                out.write(perkins_score, id="pscore")

            # Write data (json file for area averaged metrics)
            if mip == 'obs':
                outdir = os.path.join(outpath, 'metrics_results',
                                      'precip_distribution', mip, ver)
            else:
                outdir = os.path.join(
                    outpath, 'metrics_results', 'precip_distribution', mip, exp, ver)
            outfilename = outfile_metric+res+"_" + dat + ".json"            
            JSON = pcmdi_metrics.io.base.Base(outdir, outfilename)
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

            print('Complete ', met, mip, dat)
            
print('Complete all')
