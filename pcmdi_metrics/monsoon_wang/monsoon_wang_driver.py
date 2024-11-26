#!/usr/bin/env python

import collections
import os
import sys

import numpy as np
import xarray as xr

import pcmdi_metrics
from pcmdi_metrics import resources
from pcmdi_metrics.io import region_subset
from pcmdi_metrics.monsoon_wang.lib import (
    create_monsoon_wang_parser,
    mpd,
    mpi_skill_scores,
    regrid,
)
from pcmdi_metrics.utils import StringConstructor
from pcmdi_metrics.io import da_to_ds


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

    # VAR IS FIXED TO BE PRECIP FOR CALCULATING MONSOON PRECIPITATION INDICES
    var = args.modvar
    thr = args.threshold
    sig_digits = ".3f"

    # Get flag for CMEC output
    cmec = args.cmec

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
        nout_mpi_obs = os.path.join(outpathdata, "mpi_obs_masked.nc")
        da_to_ds(mpi_obs).to_netcdf(nout_mpi_obs)

    # ########################################
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
        raise RuntimeError("No model file found!")

    # ########################################

    egg_pth = resources.resource_path()

    doms = ["AllMW", "AllM", "NAMM", "SAMM", "NAFM", "SAFM", "ASM", "AUSM"]

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

        print("modelFile =  ", modelFile)
        f = xr.open_dataset(modelFile)
        d_orig = f[var]

        annrange_mod, mpi_mod = mpd(d_orig)
        domain_mask_mod = xr.where(annrange_mod > thr, 1, 0)
        mpi_mod = mpi_mod.where(domain_mask_mod)

        annrange_obs = regrid(annrange_obs, annrange_mod)
        mpi_obs = regrid(mpi_obs, mpi_mod)

        for dom in doms:
            mpi_stats_dic[mod][dom] = {}

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

            # DOMAIN SELECTED FROM GLOBAL ANNUAL RANGE FOR MODS AND OBS
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
            fm = os.path.join(nout, "_".join([mod, dom, "wang-monsoon.nc"]))
            ds_out = xr.Dataset(
                {
                    "obsmap": annrange_obs_dom,
                    "modmap": annrange_mod_dom,
                    "hitmap": hitmap,
                    "missmap": missmap,
                    "falarmmap": falarmmap,
                }
            )
            ds_out.to_netcdf(fm)
        f.close()

        if np.isnan(cor):
            print("invalid correlation values")
            sys.exit()

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


if __name__ == "__main__":
    P = create_monsoon_wang_parser()
    args = P.get_parameter(argparse_vals_only=False)
    monsoon_wang_runner(args)
