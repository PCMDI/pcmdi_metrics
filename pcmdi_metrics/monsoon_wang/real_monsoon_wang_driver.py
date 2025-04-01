#!/usr/bin/env python

import collections
import os
import sys
import glob
import re

import numpy as np
import xarray as xr

import pcmdi_metrics
from pcmdi_metrics import resources
from pcmdi_metrics.io import da_to_ds, region_subset
from pcmdi_metrics.monsoon_wang.lib import (
    create_monsoon_wang_parser,
    map_plotter,
    mpd,
    mpi_skill_scores,
    regrid,
)
from pcmdi_metrics.utils import StringConstructor

import warnings
import gc

# Suppress FutureWarnings related to MaskedConstant format strings
warnings.filterwarnings("ignore", category=FutureWarning, message=".*Format strings passed to MaskedConstant are ignored.*")
warnings.filterwarnings("ignore", message="Unable to decode time axis into full numpy.datetime64 objects")
warnings.filterwarnings("ignore", message="ESMF installation version .* ESMPy version .*")


def rlz_grep(modpath, mod, rlz_str='i1p1'):
    directory_path = os.path.dirname(modpath)
    pattern = os.path.join(directory_path, "*."+mod+".*"+rlz_str+"*AC*.nc")
    matching_files = glob.glob(pattern)
    num_fn = len(matching_files)
    pattern_extract = re.compile(r'r\d+i\d+p\d+')
    #pattern_extract = re.compile(r'r\d+i\d+p\d+f\d+')
    rlz_list = [pattern_extract.search(os.path.basename(file)).group() for file in matching_files if pattern_extract.search(os.path.basename(file))]

    return matching_files, rlz_list


def main():
    P = create_monsoon_wang_parser()
    P.add_argument('--nth', type=int, default=0, help="Specify the nth value (default is 0)")
    P.add_argument('--dom_list', type=str, default=["AllM", "NAMM", "SAMM", "NAFM", "SAFM", "SASM", "EASM", "AUSM"], help='list of domains')
    args = P.get_parameter(argparse_vals_only=False)
    monsoon_wang_runner(args)


def get_unique_filename(directory, filename):
    # Extract the base name and extension
    base_name, ext = os.path.splitext(filename)

    # Initialize the counter
    counter = 0

    # Create a new filename with a suffix if the file exists
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base_name}_{counter}{ext}"
        counter += 1

    return new_filename


def monsoon_wang_runner(args):
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

    #print("\n modpath.keys = ", modpath.keys())
    #print(" modpath() = ", modpath())
    #print("\n json_filename = ", json_filename)
    #sys.exit()

    # VAR IS FIXED TO BE PRECIP FOR CALCULATING MONSOON PRECIPITATION INDICES
    var = args.modvar
    thr = args.threshold
    sig_digits = ".3f"

    # Get flag for CMEC output
    cmec = args.cmec

    # ########################################
    # SETUP WHERE TO OUTPUT RESULTING DATA (netcdf)
    nout = os.path.join(
        outpathdata, "_".join([args.experiment, args.mip, "wang-monsoon"])
    )
    try:
        os.makedirs(nout)
    except BaseException:
        pass

    #print("nout = " , nout)

    # SETUP WHERE TO OUTPUT RESULTS (json)
    jout = outpathdata

    #print("\n jout = ", jout)
    #sys.exit()

    json_filename = get_unique_filename(jout, json_filename)
    print("\n updated json_filename  =  ", json_filename)
    
    try:
        os.makedirs(nout)
    except BaseException:
        pass

    gmods = []  # "Got" these MODS

    nth = args.nth
    for i, mod in enumerate(mods[nth:nth+1]):#, start=n):
        if nth >= len(mods):
            print("\n\n  nth >= len(mods) !!!!!!!!")
            continue
    #for i, mod in enumerate(mods[nth:nth+4]):#, start=n):
    #for i, mod in enumerate(mods):

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

        #print("\n modpath.keys = ", modpath.keys())
        #print(" modpath.model = ", modpath.model)
        #print(" modpath() = ", modpath())
        #print("\n json_filename = ", json_filename)
        #print("gmods = ", gmods)
        #sys.exit()

    if len(gmods) == 0:
        raise RuntimeError("No model file found!")

    # ########################################
    # PMP monthly default PR obs

    fobs = xr.open_dataset(args.reference_data_path, decode_times=False)
    dobs_orig = fobs[args.obsvar]
    fobs.close()

    # #######################################
    # FCN TO COMPUTE GLOBAL ANNUAL RANGE AND MONSOON PRECIP INDEX

    annrange_obs, mpi_obs = mpd(dobs_orig)

    # create monsoon domain mask based on observations: annual range > 2.5 mm/day
    if args.obs_mask:
        domain_mask_obs = xr.where(annrange_obs > thr, 1, 0)
        domain_mask_obs.name = "mask"
        mpi_obs = mpi_obs.where(domain_mask_obs)

        nout_mpi_obs = os.path.join(nout, "mpi_obs_masked.nc")
        da_to_ds(mpi_obs).to_netcdf(nout_mpi_obs)

#####        mpi_obs = mpi_obs.drop_vars("time")

    egg_pth = resources.resource_path()

    #doms = ["AllMW", "NAMM", "SAMM", "NAFM", "SAFM", "ASM", "AUSM"]
    doms = ["AllM", "NAMM", "SAMM", "NAFM", "SAFM", "SASM", "EASM", "AUSM"]
    #doms = ["NAFM"]
    doms = ["EASM"]
    doms = ["NAMM"]

    dom_list = args.dom_list
    doms = dom_list

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


        mpi_stats_dic[mod] = {}

        files, rlz_list = rlz_grep(modpath(), mod, rlz_str='i1p1')

        #print("files = ", files)
        #print("realizations = ", rlz_list)
        #sys.exit()

        for modelFile, rlz in zip(files, rlz_list):


            #modelFile = modpath()
    
            mpi_stats_dic[mod][rlz] = {}
    
            #print("\n")
            print("modelFile =  ", modelFile)
            f = xr.open_dataset(modelFile)
            d_orig = f[var]
    
            annrange_mod, mpi_mod = mpd(d_orig)
            domain_mask_mod = xr.where(annrange_mod > thr, 1, 0)
            mpi_mod = mpi_mod.where(domain_mask_mod)
    
            #print("annrange_mod = , ", annrange_mod)
            #print("mpi_mod = ", mpi_mod)
    
            try:
                mpi_mod = mpi_mod.drop_vars("time")
                annrange_mod = annrange_mod.drop_vars("time")
    #            mpi_mod = mpi_mod.squeeze(dim='time', drop=True, axis='time')
    #            annrange_mod = annrange_mod.squeeze(dim='time', drop=True, axis='time')
    #            print("XXXX drop mpi_mod time dims !!!!!!!!!! ")
            except:
                pass
    
            #print("annrange_mod = , ", annrange_mod)
            #print("mpi_mod = ", mpi_mod)
            #sys.exit()
    
    #        print("mpi_obs = ", mpi_obs)
            annrange_obs = regrid(annrange_obs, annrange_mod)
            mpi_obs = regrid(mpi_obs, mpi_mod)
    
            print("# of non-nans = ", (mpi_mod != 0).sum().values)
    #        mpi_obs.to_netcdf("mpi_obs.nc")
    
            for dom in doms:
                mpi_stats_dic[mod][rlz][dom] = {}
    
                print("dom =  ", dom)
    
                mpi_obs_reg = region_subset(mpi_obs, dom)
                mpi_obs_reg_sd = mpi_obs_reg.std(dim=["lat", "lon"])
                mpi_mod_reg = region_subset(mpi_mod, dom)
    
                da1_flat = mpi_mod_reg.values.ravel()
                da2_flat = mpi_obs_reg.values.ravel()
    
                cor = np.ma.corrcoef(
                    np.ma.masked_invalid(da1_flat), np.ma.masked_invalid(da2_flat)
                )[0, 1]
    
                squared_diff = (mpi_mod_reg - mpi_obs_reg) ** 2
                mean_squared_error = squared_diff.mean(skipna=True)
                rms = np.sqrt(mean_squared_error)
    
                rmsn = rms / mpi_obs_reg_sd
    
                for var_tmp in {'mpi_obs_reg_sd', 'mpi_mod_reg', 'squared_diff', 'rms', 'rmsn', 'da2_flat', 'cor', 'mean_squared_error', 'initial_vars', 'da1_flat', 'mpi_obs_reg'}:
                    try:
                        del var_tmp
                    except:
                        pass
    
    
                # DOMAIN SELECTED FROM GLOBAL ANNUAL RANGE FOR MODS AND OBS
                annrange_mod_dom = region_subset(annrange_mod, dom)
                annrange_obs_dom = region_subset(annrange_obs, dom)
    
                # SKILL SCORES
                #  HIT/(HIT + MISSED + FALSE ALARMS)
                hit, missed, falarm, score, hitmap, missmap, falarmmap = mpi_skill_scores(
                    annrange_mod_dom, annrange_obs_dom, thr
                )
    
                # POPULATE DICTIONARY FOR JSON FILES
                #mpi_stats_dic[mod][rlz][dom] = {}
                mpi_stats_dic[mod][rlz][dom]["cor"] = format(cor, sig_digits)
                mpi_stats_dic[mod][rlz][dom]["rmsn"] = format(rmsn, sig_digits)
                mpi_stats_dic[mod][rlz][dom]["threat_score"] = format(score, sig_digits)
    
                # SAVE ANNRANGE AND HIT MISS AND FALSE ALARM FOR EACH MOD DOM
                #fm = os.path.join(nout, "_".join([mod, dom, "wang-monsoon.nc"]))
                fm = os.path.join(nout, "_".join([mod, rlz, dom, "wang-monsoon.nc"]))
                ds_out = xr.Dataset(
                    {
                        "obsmap": annrange_obs_dom,
                        "modmap": annrange_mod_dom,
                        "hitmap": hitmap,
                        "missmap": missmap,
                        "falarmmap": falarmmap,
                        "obsmask": mpi_obs_reg,
                        "modmask": mpi_mod_reg,
                    }
                )
                ds_out.to_netcdf(fm)
    
                # PLOT FIGURES
                title = f"{mod}, {dom}"
                #save_path = os.path.join(nout, "_".join([mod, dom, "wang-monsoon.png"]))
                save_path = os.path.join(nout, "_".join([mod, rlz, dom, "wang-monsoon.png"]))
                #map_plotter(
                #    dom,
                #    title,
                #    ds_out,
                #    save_path=save_path,
                #)
    
            f.close()
    
            for var_tmp in {'d_orig', 'annrange_mod', 'mpi_mod', 'domain_mask_mod', 'annrange_obs', 'mpi_obs'}:
                try:
                    del var_tmp
                except:
                    pass
    
            if np.isnan(cor):
                print("invalid correlation values")
                sys.exit()

    print(mpi_stats_dic)
    #sys.exit()

    #  OUTPUT METRICS TO JSON FILE
    OUT = pcmdi_metrics.io.base.Base(os.path.abspath(jout), json_filename)

    disclaimer = open(os.path.join(egg_pth, "disclaimer.txt")).read()

    metrics_dictionary = collections.OrderedDict()
    metrics_dictionary["DISCLAIMER"] = disclaimer
    metrics_dictionary["REFERENCE"] = (
        "The statistics in this file are based on"
        + " Wang, B., Kim, HJ., Kikuchi, K. et al. "
        + "Diagnostic metrics for evaluation of annual and diurnal cycles. "
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


if __name__ == "__main__":
    main()
