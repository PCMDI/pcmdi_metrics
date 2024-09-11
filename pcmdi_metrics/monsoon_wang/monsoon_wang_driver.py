#!/usr/bin/env python

import collections
import os

import cdms2
import numpy
import numpy as np
from genutil import statistics

import pcmdi_metrics
from pcmdi_metrics import resources
from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
from monsoon_precip_index_fncs import mpd, mpi_skill_scores
from monsoon_precip_index_fncs import regrid, da_to_ds
from pcmdi_metrics.utils import StringConstructor
import sys
import xcdat as xc
import xarray as xr
from pcmdi_metrics.io import load_regions_specs, region_subset
#import da_to_ds


def create_monsoon_wang_parser():
    P = PMPParser()

    P.use("--modnames")
    P.use("--results_dir")
    P.use("--reference_data_path")
    P.use("--test_data_path")

    P.add_argument(
        "--outnj",
        "--outnamejson",
        type=str,
        dest="outnamejson",
        default="monsoon_wang.json",
        help="Output path for jsons",
    )
    P.add_argument(
        "-e",
        "--experiment",
        type=str,
        dest="experiment",
        default="historical",
        help="AMIP, historical or picontrol",
    )
    P.add_argument(
        "-c", "--MIP", type=str, dest="mip", default="CMIP5", help="put options here"
    )
    P.add_argument(
        "--ovar", dest="obsvar", default="pr", help="Name of variable in obs file"
    )
    P.add_argument(
        "-v",
        "--var",
        dest="modvar",
        default="pr",
        help="Name of variable in model files",
    )
    P.add_argument(
        "-t",
        "--threshold",
        default=2.5 / 86400.0,
        type=float,
        help="Threshold for a hit when computing skill score",
    )
    P.add_argument(
        "--cmec",
        dest="cmec",
        default=False,
        action="store_true",
        help="Use to save CMEC format metrics JSON",
    )
    P.add_argument(
        "--no_cmec",
        dest="cmec",
        default=False,
        action="store_false",
        help="Do not save CMEC format metrics JSON",
    )
    P.set_defaults(cmec=False)
    return P


def monsoon_wang_runner(args):
    # args = P.parse_args(sys.argv[1:])
    modpath = StringConstructor(args.test_data_path)
    modpath.variable = args.modvar
    outpathdata = args.results_dir
    if isinstance(args.modnames, str):
        mods = eval(args.modnames)
    else:
        mods = args.modnames

    json_filename = args.outnamejson

    if json_filename == "CMIP_MME":
        json_filename = "/MPI_" + args.mip + "_" + args.experiment

    # VAR IS FIXED TO BE PRECIP FOR CALCULATING MONSOON PRECIPITATION INDICES
    var = args.modvar
    thr = args.threshold
    sig_digits = ".3f"

    # Get flag for CMEC output
    cmec = args.cmec

    #########################################
    # PMP monthly default PR obs
    cdms2.axis.longitude_aliases.append("longitude_prclim_mpd")
    cdms2.axis.latitude_aliases.append("latitude_prclim_mpd")
    #fobs = cdms2.open(args.reference_data_path)
    #dobs_orig = fobs(args.obsvar)
    #fobs.close()
    print("args.reference_data_path  =  ", args.reference_data_path)
    fobs = xr.open_dataset(args.reference_data_path, decode_times=False)
    dobs_orig = fobs[args.obsvar]
    fobs.close()

    #obsgrid = dobs_orig.getGrid()
    #print(" obsgrid =  ", obsgrid)

    ########################################

    # FCN TO COMPUTE GLOBAL ANNUAL RANGE AND MONSOON PRECIP INDEX

    annrange_obs, mpi_obs = mpd(dobs_orig)
    #########################################
    # SETUP WHERE TO OUTPUT RESULTING DATA (netcdf)
    nout = os.path.join(
        outpathdata, "_".join([args.experiment, args.mip, "wang-monsoon"])
    )
    try:
        os.makedirs(nout)
    except BaseException:
        pass

    # SETUP WHERE TO OUTPUT RESULTS (json)
    jout = outpathdata
    try:
        os.makedirs(nout)
    except BaseException:
        pass

    gmods = []  # "Got" these MODS
    for i, mod in enumerate(mods):
        modpath.model = mod
        for k in modpath.keys():
            try:
                val = getattr(args, k)
            except Exception:
                continue
            if not isinstance(val, (list, tuple)):
                setattr(modpath, k, val)
            else:
                setattr(modpath, k, val[i])
        l1 = modpath()
        if os.path.isfile(l1) is True:
            gmods.append(mod)

    if len(gmods) == 0:
        print("gmods = ", gmods)
        raise RuntimeError("No model file found!")

    print("nout = ", nout)
    #print("jout = ", jout)
    print("gmods = ", gmods)
    #########################################

    egg_pth = resources.resource_path()
    globals = {}
    locals = {}
    exec(
        compile(
            open(os.path.join(egg_pth, "default_regions.py")).read(),
            os.path.join(egg_pth, "default_regions.py"),
            "exec",
        ),
        globals,
        locals,
    )

    #print("locals = ", locals)
    #print("globals = ", globals)
    print('os.path.join(egg_pth, "default_regions.py")  = ', os.path.join(egg_pth, "default_regions.py"))
    # /home/dong12/miniconda3/envs/PMP_240423/share/pmp/default_regions.py

    regions_specs = locals["regions_specs"]
    doms = ["AllMW", "AllM", "NAMM", "SAMM", "NAFM", "SAFM", "ASM", "AUSM"]
    #doms = ["AllMW"]#, "AllM", "NAMM", "SAMM", "NAFM", "SAFM", "ASM", "AUSM"]
    #doms = ["AUSM"]
    #doms = ["NAMM"]
    #doms = ["NAFM"]
    
    #print('region_specs = ',regions_specs)
    #print('region_specs["AllMW"] = ',regions_specs['AllMW'])
    #print('region_specs["AllMW"]["domain"] = ',regions_specs['AllMW']['domain'])
    #print('region_specs["AllM"]["domain"] = ',regions_specs['AllM']['domain'])
    #print('region_specs["ASM"]["domain"] = ',regions_specs['ASM']['domain'])


    #sys.exit()


    mpi_stats_dic = {}
    for i, mod in enumerate(gmods):
        modpath.model = mod
        for k in modpath.keys():
            try:
                val = getattr(args, k)
            except Exception:
                continue
            if not isinstance(val, (list, tuple)):
                setattr(modpath, k, val)
            else:
                setattr(modpath, k, val[i])
        modelFile = modpath()

        mpi_stats_dic[mod] = {}

        print(
            "******************************************************************************************"
        )
        print("modelFile =  ", modelFile)
        #f = cdms2.open(modelFile)
        #d_orig = f(var)
        f = xr.open_dataset(modelFile)
        d_orig = f[var]


        annrange_mod, mpi_mod = mpd(d_orig)

        #print('mod_annrange.dims = ', annrange_mod.dims)
        #print('obs_annrange_dims = ', annrange_obs.dims)
        #print('mod_annrange.coords = ', annrange_mod.coords)
        #print('obs_annrange_coords = ', annrange_obs.coords)


#        sys.exit()

#        annrange_mod = annrange_mod.regrid(
#            obsgrid, regridTool="regrid2", regridMethod="conserve", mkCyclic=True
#        )
#        mpi_mod = mpi_mod.regrid(
#            obsgrid, regridTool="regrid2", regridMethod="conserve", mkCyclic=True
#        )

        #print('annrange_obs =  ', annrange_obs)
        lats = annrange_obs.lat[0]
        latn = annrange_obs.lat[-1]
        lone = annrange_obs.lon[-1]
        lonw = annrange_obs.lon[0]

        #annrange_obs.to_netcdf("annrange_obs.nc")

        #annrange_obs = annrange_obs.interp(lat=mpi_mod.lat, lon=mpi_mod.lon, method='linear')
        annrange_obs = regrid(annrange_obs, annrange_mod)
        
        #annrange_obs.to_netcdf("annrange_obs_interp.nc")

        #print('annrange_obs =  ', annrange_obs)
        #print('annrange_obs =  ', annrange_obs.sel(lat=slice(lats, latn), lon=slice(lonw, lone)))

        #mpi_obs = mpi_obs.interp(lat=mpi_mod.lat, lon=mpi_mod.lon, method='linear')
        mpi_obs = regrid(mpi_obs, mpi_mod)


        #print("mpi_obs = ", mpi_obs)


        regions_specs = load_regions_specs()
        #print("regions_specs - ", regions_specs)
        print("list(regions_specs.keys())",  list(regions_specs.keys()))

        for dom in doms:
            mpi_stats_dic[mod][dom] = {}

            #reg_sel = regions_specs[dom]["domain"]

            print("dom =  ", dom)

            #mpi_obs.to_netcdf("xd_mpi_obs.nc")

            mpi_obs_reg = region_subset(mpi_obs, dom, data_var="pr", regions_specs=regions_specs)
            #mpi_obs_reg = region_subset(mpi_obs, dom)#, var="pr", regions_specs=regions_specs)
            #mpi_obs_reg = region_subset(mpi_obs, dom, var="pr")#, regions_specs=regions_specs)
            #mpi_obs_reg = region_subset(mpi_obs, regions_specs, region=dom)#, var="pr", regions_specs=regions_specs)
            #mpi_obs_reg = region_subset(mpi_obs, regions_specs=regions_specs, region=dom)

            #print("mpi_obs_reg =  ", mpi_obs_reg)
            #sys.exit()

            #mpi_obs_reg = mpi_obs(reg_sel)

            #mpi_obs_reg_sd = float(statistics.std(mpi_obs_reg, axis="xy"))
            mpi_obs_reg_sd = mpi_obs_reg.std(dim=['lat', 'lon'])

            #mpi_mod_reg = mpi_mod(reg_sel)
            #mpi_mod_reg = region_subset(mpi_mod, regions_specs=regions_specs, region=dom)
            mpi_mod_reg = region_subset(mpi_mod, dom)

            #cor = float(statistics.correlation(mpi_mod_reg, mpi_obs_reg, axis="xy"))
            da1_flat = mpi_mod_reg.values.ravel()
            da2_flat = mpi_obs_reg.values.ravel()
            #print("da1_flat = ", da1_flat)
            #print("da2_flat = ", da2_flat)
            cor = np.corrcoef(da1_flat, da2_flat)[0, 1]
            print("cor = ", cor)
            #sys.exit()

            #rms = float(statistics.rms(mpi_mod_reg, mpi_obs_reg, axis="xy"))
            squared_diff = (mpi_mod_reg - mpi_obs_reg) ** 2
            mean_squared_error = squared_diff.mean(skipna=True)
            rms = np.sqrt(mean_squared_error)

            rmsn = rms / mpi_obs_reg_sd
            del(mpi_mod_reg)

            #  DOMAIN SELECTED FROM GLOBAL ANNUAL RANGE FOR MODS AND OBS
            #annrange_mod_dom = annrange_mod(reg_sel)
            #annrange_obs_dom = annrange_obs(reg_sel)

            #annrange_mod_dom = region_subset(annrange_mod, regions_specs=regions_specs, region=dom)
            #annrange_obs_dom = region_subset(annrange_obs, regions_specs=regions_specs, region=dom)
            annrange_mod_dom = region_subset(annrange_mod, dom)
            annrange_obs_dom = region_subset(annrange_obs, dom)

            # SKILL SCORES
            #  HIT/(HIT + MISSED + FALSE ALARMS)
            hit, missed, falarm, score, hitmap, missmap, falarmmap = mpi_skill_scores(
                annrange_mod_dom, annrange_obs_dom, thr
            )

            #  POPULATE DICTIONARY FOR JSON FILES
            mpi_stats_dic[mod][dom] = {}
            mpi_stats_dic[mod][dom]["cor"] = format(cor, sig_digits)
            mpi_stats_dic[mod][dom]["rmsn"] = format(rmsn, sig_digits)
            mpi_stats_dic[mod][dom]["threat_score"] = format(score, sig_digits)

            # SAVE ANNRANGE AND HIT MISS AND FALSE ALARM FOR EACH MOD DOM
            fm = os.path.join(nout, "_".join([mod, dom, "wang-monsoon_xcdat.nc"]))
            #g = cdms2.open(fm, "w")
            #g.write(annrange_mod_dom)
            #g.write(hitmap, dtype=numpy.int32)
            #g.write(missmap, dtype=numpy.int32)
            #g.write(falarmmap, dtype=numpy.int32)
            #g.close()
            ds_out = xr.Dataset({
                    "hitmap": hitmap,
                    "missmap": missmap,
                    "falarmmap": falarmmap
                    })
            ds_out.to_netcdf(fm)
        f.close()

    #  OUTPUT METRICS TO JSON FILE
    OUT = pcmdi_metrics.io.base.Base(os.path.abspath(jout), json_filename)

    disclaimer = open(os.path.join(egg_pth, "disclaimer.txt")).read()

    metrics_dictionary = collections.OrderedDict()
    metrics_dictionary["DISCLAIMER"] = disclaimer
    metrics_dictionary["REFERENCE"] = (
        "The statistics in this file are based on"
        + " Wang, B., Kim, HJ., Kikuchi, K. et al. "
        + "Clim Dyn (2011) 37: 941. doi:10.1007/s00382-010-0877-0"
    )
    metrics_dictionary["RESULTS"] = mpi_stats_dic  # collections.OrderedDict()

    OUT.var = var
    OUT.write(
        metrics_dictionary,
        json_structure=["model", "domain", "statistic"],
        indent=4,
        separators=(",", ": "),
    )
    if cmec:
        print("Writing cmec file")
        OUT.write_cmec(indent=4, separators=(",", ": "))
