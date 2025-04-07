#!/usr/bin/env python

import collections
import os
import sys
import warnings

import numpy as np
import xarray as xr

import pcmdi_metrics
from pcmdi_metrics import resources
from pcmdi_metrics.io import da_to_ds, region_subset, xcdat_open
from pcmdi_metrics.monsoon_wang.lib import (
    create_monsoon_wang_parser,
    map_plotter,
    mpd,
    mpi_skill_scores,
    regrid,
    save_to_netcdf_with_attributes,
)
from pcmdi_metrics.utils import StringConstructor

# Suppress FutureWarnings related to MaskedConstant format strings
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*Format strings passed to MaskedConstant are ignored.*",
)
warnings.filterwarnings(
    "ignore", message="Unable to decode time axis into full numpy.datetime64 objects"
)


def main():
    P = create_monsoon_wang_parser()
    P.add_argument(
        "--nth", type=int, default=0, help="Specify the nth value (default is 0)"
    )
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
        json_filename = f"MPI_{args.mip}_{args.experiment}"

    # VAR IS FIXED TO BE PRECIP FOR CALCULATING MONSOON PRECIPITATION INDICES
    var = args.modvar
    thr = args.threshold
    sig_digits = ".3f"

    # Get flag for CMEC output
    cmec = args.cmec

    # ---------------------------------------------
    # SETUP WHERE TO OUTPUT RESULTING DATA (netcdf)
    # ---------------------------------------------
    nout = outpathdata
    if not os.path.exists(nout):
        try:
            os.makedirs(nout)
        except BaseException:
            pass

    # SETUP WHERE TO OUTPUT RESULTS (json)
    jout = outpathdata

    json_filename = get_unique_filename(jout, json_filename)
    print("\n updated json_filename  =  ", json_filename)

    if not os.path.exists(jout):
        try:
            os.makedirs(jout)
        except BaseException:
            pass

    gmods = []  # "Got" these MODS

    nth = args.nth
    for i, mod in enumerate(mods[nth : nth + 4]):  # , start=n):
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

    # --------------------------
    # PMP monthly default PR obs
    # --------------------------
    print("obs file:", args.reference_data_path)

    # Check if the reference data path is provided
    if not os.path.exists(args.reference_data_path):
        raise FileNotFoundError(
            f"Reference data file not found: {args.reference_data_path}"
        )

    # Open the reference data file
    try:
        ds_obs = xcdat_open(args.reference_data_path)
    except (ValueError, OSError) as e:
        print(
            f"Error opening reference data file with decode_times=True: {e}. Trying with decode_times=False..."
        )
        ds_obs = xcdat_open(args.reference_data_path, decode_times=False)

    # -----------------------------------------------------------
    # FCN TO COMPUTE GLOBAL ANNUAL RANGE AND MONSOON PRECIP INDEX
    # -----------------------------------------------------------
    annrange_obs, mpi_obs = mpd(ds_obs, data_var=args.obsvar)

    # create monsoon domain mask based on observations: annual range > 2.5 mm/day
    if args.obs_mask:
        domain_mask_obs = xr.where(annrange_obs > thr, 1, 0)
        domain_mask_obs.name = "mask"
        mpi_obs = mpi_obs.where(domain_mask_obs)

        nout_mpi_obs = os.path.join(nout, "mpi_obs_masked.nc")

        ds_mpi_obs = da_to_ds(mpi_obs, var=f"masked_{args.obsvar}")

        # Save to netcdf
        save_to_netcdf_with_attributes(
            ds_mpi_obs, ds_obs, args.reference_data_path, nout_mpi_obs
        )

    egg_pth = resources.resource_path()

    # doms = ["AllM", "NAMM", "SAMM", "NAFM", "SAFM", "SASM", "EASM", "AUSM"]
    doms = ["AllM", "NAMM", "SAMM", "NAFM", "SAFM", "ASM", "AUSM"]

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

        print("modelFile: ", modelFile)
        ds_model = xcdat_open(modelFile)

        annrange_mod, mpi_mod = mpd(ds_model, data_var=var)
        domain_mask_mod = xr.where(annrange_mod > thr, 1, 0)
        mpi_mod = mpi_mod.where(domain_mask_mod)

        try:
            mpi_mod = mpi_mod.drop_vars("time")
            annrange_mod = annrange_mod.drop_vars("time")
        except Exception:
            pass

        annrange_obs = regrid(annrange_obs, annrange_mod)
        mpi_obs = regrid(mpi_obs, mpi_mod)

        for dom in doms:
            mpi_stats_dic[mod][dom] = {}

            print("domain: ", dom)

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

            for var_name in {
                "mpi_obs_reg_sd",
                "mpi_mod_reg",
                "squared_diff",
                "rms",
                "rmsn",
                "da2_flat",
                "cor",
                "mean_squared_error",
                "da1_flat",
                "mpi_obs_reg",
            }:
                try:
                    del globals()[var_name]
                except KeyError:
                    pass

            # DOMAIN SELECTED FROM GLOBAL ANNUAL RANGE FOR MODS AND OBS
            annrange_mod_dom = region_subset(annrange_mod, dom)
            annrange_obs_dom = region_subset(annrange_obs, dom)

            # SKILL SCORES
            # HIT/(HIT + MISSED + FALSE ALARMS)
            hit, missed, falarm, score, hitmap, missmap, falarmmap = mpi_skill_scores(
                annrange_mod_dom, annrange_obs_dom, thr
            )

            # POPULATE DICTIONARY FOR JSON FILES
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
                    "obsmask": mpi_obs_reg,
                    "modmask": mpi_mod_reg,
                }
            )
            ds_out.to_netcdf(fm)

            # PLOT FIGURES
            title = f"{mod}, {dom}"
            save_path = os.path.join(nout, "_".join([mod, dom, "wang-monsoon.png"]))
            map_plotter(
                dom,
                title,
                ds_out,
                save_path=save_path,
            )

        ds_model.close()

        for var_name in {
            "annrange_mod",
            "mpi_mod",
            "domain_mask_mod",
            "annrange_obs",
            "mpi_obs",
        }:
            try:
                del globals()[var_name]
            except KeyError:
                pass

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
