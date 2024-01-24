#!/usr/bin/env python

"""
# Modes of Variability Metrics
- Calculate metrics for modes of varibility from archive of CMIP models
- Author: Jiwoo Lee (lee1043@llnl.gov), PCMDI, LLNL

## EOF1 based variability modes
- NAM: Northern Annular Mode
- NAO: Northern Atlantic Oscillation
- SAM: Southern Annular Mode
- PNA: Pacific North American Pattern
- PDO: Pacific Decadal Oscillation

## EOF2 based variability modes
- NPO: North Pacific Oscillation (2nd EOFs of PNA domain)
- NPGO: North Pacific Gyre Oscillation (2nd EOFs of PDO domain)

## Reference:
Lee, J., K. Sperber, P. Gleckler, C. Bonfils, and K. Taylor, 2019:
Quantifying the Agreement Between Observed and Simulated Extratropical Modes of
Interannual Variability. Climate Dynamics.
https://doi.org/10.1007/s00382-018-4355-4

## Auspices:
This work was performed under the auspices of the U.S. Department of
Energy by Lawrence Livermore National Laboratory under Contract
DE-AC52-07NA27344. Lawrence Livermore National Laboratory is operated by
Lawrence Livermore National Security, LLC, for the U.S. Department of Energy,
National Nuclear Security Administration under Contract DE-AC52-07NA27344.

## Disclaimer:
This document was prepared as an account of work sponsored by an
agency of the United States government. Neither the United States government
nor Lawrence Livermore National Security, LLC, nor any of their employees
makes any warranty, expressed or implied, or assumes any legal liability or
responsibility for the accuracy, completeness, or usefulness of any
information, apparatus, product, or process disclosed, or represents that its
use would not infringe privately owned rights. Reference herein to any specific
commercial product, process, or service by trade name, trademark, manufacturer,
or otherwise does not necessarily constitute or imply its endorsement,
recommendation, or favoring by the United States government or Lawrence
Livermore National Security, LLC. The views and opinions of authors expressed
herein do not necessarily state or reflect those of the United States
government or Lawrence Livermore National Security, LLC, and shall not be used
for advertising or product endorsement purposes.
"""
# import shapely  # noqa

import glob
import json
import os
import re
import sys
from argparse import RawTextHelpFormatter
from shutil import copyfile

from pcmdi_metrics.io import fill_template, get_grid, load_regions_specs, region_subset
from pcmdi_metrics.mean_climate.lib import pmp_parser
from pcmdi_metrics.stats import calculate_temporal_correlation as calcTCOR
from pcmdi_metrics.stats import mean_xy
from pcmdi_metrics.utils import regrid, sort_human, tree
from pcmdi_metrics.variability_mode.lib import (
    AddParserArgument,
    VariabilityModeCheck,
    YearCheck,
    adjust_timeseries,
    calc_stats_save_dict,
    calcSTD,
    check_start_end_year,
    debug_print,
    eof_analysis_get_variance_mode,
    gain_pcs_fraction,
    gain_pseudo_pcs,
    linear_regression_on_globe_for_teleconnection,
    north_test,
    plot_map,
    read_data_in,
    variability_metrics_to_json,
    write_nc_output,
)

# =================================================
# Collect user defined options
# -------------------------------------------------
P = pmp_parser.PMPParser(
    description="Runs PCMDI Modes of Variability Computations",
    formatter_class=RawTextHelpFormatter,
)
P = AddParserArgument(P)
param = P.get_parameter()

# Pre-defined options
mip = param.mip
exp = param.exp
fq = param.frequency
realm = param.realm
print("mip:", mip)
print("exp:", exp)
print("fq:", fq)
print("realm:", realm)

# On/off switches
obs_compare = True  # Statistics against observation
CBF = param.CBF  # Conduct CBF analysis
ConvEOF = param.ConvEOF  # Conduct conventional EOF analysis

EofScaling = param.EofScaling  # If True, consider EOF with unit variance
RmDomainMean = param.RemoveDomainMean  # If True, remove Domain Mean of each time step
LandMask = param.landmask  # If True, maskout land region thus consider only over ocean

print("EofScaling:", EofScaling)
print("RmDomainMean:", RmDomainMean)
print("LandMask:", LandMask)

nc_out_obs = param.nc_out_obs  # Record NetCDF output
plot_obs = param.plot_obs  # Generate plots
nc_out_model = param.nc_out  # Record NetCDF output
plot_model = param.plot  # Generate plots
update_json = param.update_json

print("nc_out_obs, plot_obs:", nc_out_obs, plot_obs)
print("nc_out_model, plot_model:", nc_out_model, plot_model)

cmec = False
if hasattr(param, "cmec"):
    cmec = param.cmec  # Generate CMEC compliant json
print("CMEC:" + str(cmec))

# Check given mode of variability
mode = VariabilityModeCheck(param.variability_mode, P)
print("mode:", mode)

# Variables
var = param.varModel

# Check dependency for given season option
seasons = param.seasons
print("seasons:", seasons)

# Observation information
obs_name = param.reference_data_name
obs_path = param.reference_data_path
obs_var = param.varOBS

# Path to model data as string template
modpath = param.modpath
if LandMask:
    modpath_lf = param.modpath_lf

# Check given model option
models = param.modnames

# Include all models if conditioned
if ("all" in [m.lower() for m in models]) or (models == "all"):
    model_index_path = re.split("[._]", modpath.split("/")[-1]).index("%(model)")
    models = [
        re.split("[._]", p.split("/")[-1])[model_index_path]
        for p in glob.glob(
            fill_template(
                modpath, mip=mip, exp=exp, model="*", realization="*", variable=var
            )
        )
    ]
    # remove duplicates
    models = sorted(list(dict.fromkeys(models)), key=lambda s: s.lower())

print("models:", models)
print("number of models:", len(models))

# Realizations
realization = param.realization
print("realization: ", realization)

# EOF ordinal number
eofn_obs = int(param.eofn_obs)
eofn_mod = int(param.eofn_mod)

# case id
case_id = param.case_id

# Debug
debug = param.debug

# Year
msyear = param.msyear
meyear = param.meyear
YearCheck(msyear, meyear, P)

osyear = param.osyear
oeyear = param.oeyear
YearCheck(osyear, oeyear, P)

# Units adjustment
ObsUnitsAdjust = param.ObsUnitsAdjust
ModUnitsAdjust = param.ModUnitsAdjust

# lon1_global and lon2_global is for global map plotting
if mode in ["PDO", "NPGO"]:
    lon1_global = 0
    lon2_global = 360
else:
    lon1_global = -180
    lon2_global = 180

# parallel
parallel = param.parallel
print("parallel:", parallel)

# =================================================
# Time period adjustment
# -------------------------------------------------
if osyear is None:
    osyear = msyear

if oeyear is None:
    oeyear = meyear

# =================================================
# Region control
# -------------------------------------------------
regions_specs = load_regions_specs()

# =================================================
# Create output directories
# -------------------------------------------------
outdir_template = param.results_dir

output_types = ["graphics", "diagnostic_results", "metrics_results"]
dir_paths = {}

print("output directories:")

for output_type in output_types:
    dir_path = fill_template(
        outdir_template,
        output_type=output_type,
        mip=mip,
        exp=exp,
        variability_mode=mode,
        reference_data_name=obs_name,
        case_id=case_id,
    )
    os.makedirs(dir_path, exist_ok=True)
    print(output_type, ":", dir_path)
    dir_paths[output_type] = dir_path

# =================================================
# Set dictionary for .json record
# -------------------------------------------------
result_dict = tree()

# Set metrics output JSON file
json_filename = "_".join(
    [
        "var",
        "mode",
        mode,
        "EOF" + str(eofn_mod),
        "stat",
        mip,
        exp,
        fq,
        realm,
        str(msyear) + "-" + str(meyear),
    ]
)
json_file = os.path.join(dir_paths["metrics_results"], json_filename + ".json")

json_file_org = os.path.join(
    dir_paths["metrics_results"],
    "_".join([json_filename, "org", str(os.getpid())]) + ".json",
)

# Archive if there is pre-existing JSON: preventing overwriting
if os.path.isfile(json_file) and os.stat(json_file).st_size > 0:
    copyfile(json_file, json_file_org)
    if update_json:
        fj = open(json_file)
        result_dict = json.loads(fj.read())
        fj.close()

if "REF" not in result_dict:
    result_dict["REF"] = {}
if "RESULTS" not in result_dict:
    result_dict["RESULTS"] = {}

# =================================================
# Observation
# -------------------------------------------------
if obs_compare:
    obs_lf_path = None

    # read data in
    obs_timeseries = read_data_in(
        obs_path,
        obs_lf_path,
        obs_var,
        var,
        osyear,
        oeyear,
        ObsUnitsAdjust,
        LandMask,
        debug=debug,
    )

    # Save global grid information for regrid below
    ref_grid_global = get_grid(obs_timeseries)

    # Declare dictionary variables to keep information from observation
    eof_obs = {}
    pc_obs = {}
    frac_obs = {}
    solver_obs = {}
    reverse_sign_obs = {}
    eof_lr_obs = {}
    stdv_pc_obs = {}
    obs_timeseries_season_dict = {}

    # Dictonary for json archive
    if "obs" not in result_dict["REF"]:
        result_dict["REF"]["obs"] = {}
    if "defaultReference" not in result_dict["REF"]["obs"]:
        result_dict["REF"]["obs"]["defaultReference"] = {}
    if "source" not in result_dict["REF"]["obs"]["defaultReference"]:
        result_dict["REF"]["obs"]["defaultReference"]["source"] = {}
    if mode not in result_dict["REF"]["obs"]["defaultReference"]:
        result_dict["REF"]["obs"]["defaultReference"][mode] = {}

    result_dict["REF"]["obs"]["defaultReference"]["source"] = obs_path
    result_dict["REF"]["obs"]["defaultReference"]["reference_eofs"] = eofn_obs
    result_dict["REF"]["obs"]["defaultReference"]["period"] = (
        str(osyear) + "-" + str(oeyear)
    )

    # -------------------------------------------------
    # Season loop
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    debug_print("obs season loop starts", debug)

    for season in seasons:
        debug_print("season: " + season, debug)

        if season not in result_dict["REF"]["obs"]["defaultReference"][mode]:
            result_dict["REF"]["obs"]["defaultReference"][mode][season] = {}

        dict_head_obs = result_dict["REF"]["obs"]["defaultReference"][mode][season]

        # Time series adjustment (remove annual cycle, seasonal mean (if needed),
        # and subtracting domain (or global) mean of each time step)
        debug_print("time series adjustment", debug)
        obs_timeseries_season = adjust_timeseries(
            obs_timeseries, obs_var, mode, season, regions_specs, RmDomainMean
        )

        # Extract subdomain
        obs_timeseries_season_subdomain = region_subset(
            obs_timeseries_season, mode, regions_specs
        )

        # EOF analysis
        debug_print("EOF analysis", debug)
        (
            eof_obs[season],
            pc_obs[season],
            frac_obs[season],
            reverse_sign_obs[season],
            solver_obs[season],
        ) = eof_analysis_get_variance_mode(
            mode,
            obs_timeseries_season_subdomain,
            obs_var,
            eofn=eofn_obs,
            debug=debug,
            EofScaling=EofScaling,
        )

        # Calculate stdv of pc time series
        debug_print("calculate stdv of pc time series", debug)
        stdv_pc_obs[season] = calcSTD(pc_obs[season])

        # Linear regression to have extended global map; teleconnection purpose
        (
            eof_lr_obs_season,
            slope_obs,
            intercept_obs,
        ) = linear_regression_on_globe_for_teleconnection(
            pc_obs[season],
            obs_timeseries_season,
            obs_var,
            stdv_pc_obs[season],
            RmDomainMean,
            EofScaling,
            debug=debug,
        )

        obs_timeseries_season["eof_lr"] = eof_lr_obs_season
        obs_timeseries_season["slope"] = slope_obs
        obs_timeseries_season["intercept"] = intercept_obs

        obs_timeseries_season_dict[season] = obs_timeseries_season

        # Extract subdomain for plot
        obs_timeseries_season_region = region_subset(
            obs_timeseries_season, mode, regions_specs=regions_specs
        )
        eof_lr_obs[season] = eof_lr_obs_season
        # - - - - - - - - - - - - - - - - - - - - - - - - -
        # Record results
        # . . . . . . . . . . . . . . . . . . . . . . . . .
        debug_print("record results", debug)

        # Set output file name for NetCDF and plot
        output_filename_obs = (
            f"{mode}_{var}_EOF{eofn_obs}_{season}_obs_{osyear}-{oeyear}"
        )

        if EofScaling:
            output_filename_obs += "_EOFscaled"

        # Plot
        if plot_obs:
            debug_print("plot obs", debug)
            output_img_file_obs = os.path.join(
                dir_paths["graphics"], output_filename_obs
            )

            plot_map(
                mode,
                "[REF] " + obs_name,
                osyear,
                oeyear,
                season,
                obs_timeseries_season_region["eof_lr"],
                frac_obs[season],
                output_img_file_obs,
                debug=debug,
            )
            plot_map(
                mode + "_teleconnection",
                "[REF] " + obs_name,
                osyear,
                oeyear,
                season,
                # eof_lr_obs[season](longitude=(lon1_global, lon2_global)),
                eof_lr_obs_season,
                frac_obs[season],
                output_img_file_obs + "_teleconnection",
                debug=debug,
            )
            debug_print("obs plotting end", debug)

        # NetCDF: Save global map, pc timeseries, and fraction in NetCDF output
        if nc_out_obs:
            debug_print("write obs nc", debug)
            output_nc_file_obs = os.path.join(
                dir_paths["diagnostic_results"], output_filename_obs
            )
            write_nc_output(
                output_nc_file_obs,
                # eof_lr_obs[season],
                eof_lr_obs_season,
                pc_obs[season],
                frac_obs[season],
                slope_obs,
                intercept_obs,
            )

        # Save stdv of PC time series in dictionary
        dict_head_obs["stdv_pc"] = stdv_pc_obs[season]
        dict_head_obs["frac"] = float(frac_obs[season])

        # Mean
        mean_obs = mean_xy(eof_obs[season])
        mean_glo_obs = mean_xy(eof_lr_obs[season])
        dict_head_obs["mean"] = float(mean_obs)
        dict_head_obs["mean_glo"] = float(mean_glo_obs)
        debug_print("obs mean end", debug)

        # North test
        north_test(
            solver_obs[season],
            mode,
            season,
            obs_name,
            osyear,
            oeyear,
            dir_paths["diagnostic_results"],
        )

    debug_print("obs end", debug)

# =================================================
# Model
# -------------------------------------------------
for model in models:
    print(" ----- ", model, " ---------------------")

    if model not in result_dict["RESULTS"]:
        result_dict["RESULTS"][model] = {}

    model_path_list = glob.glob(
        fill_template(
            modpath,
            mip=mip,
            exp=exp,
            model=model,
            realization=realization,
            variable=var,
        )
    )

    model_path_list = sort_human(model_path_list)

    debug_print("model_path_list: " + str(model_path_list), debug)

    # Find where run can be gripped from given filename template for modpath
    if realization == "*":
        run_in_modpath = re.split(
            "[._]",
            fill_template(
                modpath,
                mip=mip,
                exp=exp,
                model=model,
                realization=realization,
                variable=var,
            ).split("/")[-1],
        ).index(realization)

    # -------------------------------------------------
    # Run
    # -------------------------------------------------
    for model_path in model_path_list:
        # try:
        if 1:
            if realization == "*":
                run = re.split("[._]", (model_path.split("/")[-1]).split("."))[
                    run_in_modpath
                ]
            else:
                run = realization
            print(" --- ", run, " ---")

            if run not in result_dict["RESULTS"][model]:
                result_dict["RESULTS"][model][run] = {}

            if "defaultReference" not in result_dict["RESULTS"][model][run]:
                result_dict["RESULTS"][model][run]["defaultReference"] = {}

            if mode not in result_dict["RESULTS"][model][run]["defaultReference"]:
                result_dict["RESULTS"][model][run]["defaultReference"][mode] = {}

            result_dict["RESULTS"][model][run]["defaultReference"][mode][
                "target_model_eofs"
            ] = eofn_mod

            if LandMask:
                model_lf_path = fill_template(modpath_lf, mip=mip, exp=exp, model=model)
            else:
                model_lf_path = None

            # read data in
            model_timeseries = read_data_in(
                model_path,
                model_lf_path,
                var,
                var,
                msyear,
                meyear,
                ModUnitsAdjust,
                LandMask=LandMask,
                debug=debug,
            )

            msyear, meyear = check_start_end_year(model_timeseries)

            debug_print("msyear: " + str(msyear) + " meyear: " + str(meyear), debug)

            # -------------------------------------------------
            # Season loop
            # - - - - - - - - - - - - - - - - - - - - - - - - -
            for season in seasons:
                debug_print("season: " + season, debug)

                if (
                    season
                    not in result_dict["RESULTS"][model][run]["defaultReference"][mode]
                ):
                    result_dict["RESULTS"][model][run]["defaultReference"][mode][
                        season
                    ] = {}
                result_dict["RESULTS"][model][run]["defaultReference"][mode][season][
                    "period"
                ] = (str(msyear) + "-" + str(meyear))

                # Time series adjustment (remove annual cycle, seasonal mean (if needed),
                # and subtracting domain (or global) mean of each time step)
                debug_print("time series adjustment", debug)
                model_timeseries_season = adjust_timeseries(
                    model_timeseries, var, mode, season, regions_specs, RmDomainMean
                )

                # Extract subdomain
                debug_print("extract subdomain", debug)
                # model_timeseries_season_subdomain = model_timeseries_season(
                #    region_subdomain
                # )
                model_timeseries_season_subdomain = region_subset(
                    model_timeseries_season, mode, regions_specs
                )

                # -------------------------------------------------
                # Common Basis Function Approach
                # - - - - - - - - - - - - - - - - - - - - - - - - -
                if CBF and obs_compare:
                    if (
                        "cbf"
                        not in result_dict["RESULTS"][model][run]["defaultReference"][
                            mode
                        ][season]
                    ):
                        result_dict["RESULTS"][model][run]["defaultReference"][mode][
                            season
                        ]["cbf"] = {}
                    dict_head = result_dict["RESULTS"][model][run]["defaultReference"][
                        mode
                    ][season]["cbf"]
                    debug_print("CBF approach start", debug)

                    # Regrid (interpolation, model grid to ref grid)
                    # model_timeseries_season_regrid = model_timeseries_season.regrid(
                    #    ref_grid_global, regridTool="regrid2", mkCyclic=True
                    # )
                    model_timeseries_season_regrid = regrid(
                        model_timeseries_season, var, ref_grid_global
                    )
                    # model_timeseries_season_regrid_subdomain = (
                    #    model_timeseries_season_regrid(region_subdomain)
                    # )
                    model_timeseries_season_regrid_subdomain = region_subset(
                        model_timeseries_season_regrid, mode, regions_specs
                    )

                    # Matching model's missing value location to that of observation
                    """
                    # Save axes for preserving
                    # axes = model_timeseries_season_regrid_subdomain.getAxisList()
                    axes = get_axis_list(model_timeseries_season_regrid_subdomain)
                    # 1) Replace model's masked grid to 0, so theoritically won't affect to result
                    model_timeseries_season_regrid_subdomain = MV2.array(
                        model_timeseries_season_regrid_subdomain.filled(0.0)
                    )
                    # 2) Give obs's mask to model field, so enable projecField functionality below
                    model_timeseries_season_regrid_subdomain.mask = eof_obs[season].mask
                    # Preserve axes
                    model_timeseries_season_regrid_subdomain.setAxisList(axes)
                    """

                    # CBF PC time series
                    cbf_pc = gain_pseudo_pcs(
                        solver_obs[season],
                        model_timeseries_season_regrid_subdomain[var],
                        eofn_obs,
                        reverse_sign_obs[season],
                        EofScaling=EofScaling,
                    )

                    # Calculate stdv of cbf pc time series
                    stdv_cbf_pc = calcSTD(cbf_pc)

                    # Linear regression to have extended global map; teleconnection purpose
                    (
                        eof_lr_cbf,
                        slope_cbf,
                        intercept_cbf,
                    ) = linear_regression_on_globe_for_teleconnection(
                        cbf_pc,
                        model_timeseries_season,
                        var,
                        stdv_cbf_pc,
                        RmDomainMean,
                        EofScaling,
                        debug=debug,
                    )

                    model_timeseries_season["eof_lr_cbf"] = eof_lr_cbf
                    model_timeseries_season["slope_cbf"] = slope_cbf
                    model_timeseries_season["intercept_cbf"] = intercept_cbf

                    # Extract subdomain for statistics
                    # eof_lr_cbf_subdomain = eof_lr_cbf(region_subdomain)
                    model_timeseries_season_subdomain = region_subset(
                        model_timeseries_season,
                        mode,
                        regions_specs=regions_specs,
                    )

                    # Calculate fraction of variance explained by cbf pc (native grid)
                    frac_cbf = gain_pcs_fraction(
                        model_timeseries_season_subdomain[var],
                        model_timeseries_season_subdomain["eof_lr_cbf"],
                        cbf_pc / stdv_cbf_pc,
                        debug=debug,
                    )

                    # SENSITIVITY TEST ---
                    # Calculate fraction of variance explained by cbf pc (regrid domain)
                    frac_cbf_regrid = gain_pcs_fraction(
                        model_timeseries_season_regrid_subdomain[var],
                        model_timeseries_season_subdomain["eof_lr_cbf"],
                        cbf_pc / stdv_cbf_pc,
                        debug=debug,
                    )
                    dict_head["frac_cbf_regrid"] = float(frac_cbf_regrid)

                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Record results
                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Metrics results -- statistics to JSON
                    common_args_cbf = {
                        "mode": mode,
                        "dict_head": dict_head,
                        "model_ds": model_timeseries_season,
                        "model_data_var": "eof_lr_cbf",
                        "eof": model_timeseries_season_subdomain["eof_lr_cbf"],
                        "eof_lr": eof_lr_cbf,
                        "pc": cbf_pc,
                        "stdv_pc": stdv_cbf_pc,
                        "frac": frac_cbf,
                        "regions_specs": regions_specs,
                        "obs_ds": obs_timeseries_season_dict[season],
                        "eof_obs": eof_obs[season],
                        "eof_lr_obs": eof_lr_obs[season],
                        "stdv_pc_obs": stdv_pc_obs[season],
                        "obs_compare": obs_compare,
                        "method": "cbf",
                        "debug": debug,
                    }

                    dict_head, eof_lr_cbf = calc_stats_save_dict(**common_args_cbf)

                    # Set output file name for NetCDF and plot images
                    output_filename = f"{mode}_{var}_EOF{eofn_mod}_{season}_{mip}_{model}_{exp}_{run}_{fq}_{realm}_{msyear}-{meyear}"
                    if EofScaling:
                        output_filename += "_EOFscaled"

                    # Diagnostics results -- data to NetCDF
                    # Save global map, pc timeseries, and fraction in NetCDF output
                    output_nc_file = os.path.join(
                        dir_paths["diagnostic_results"], output_filename
                    )
                    if nc_out_model:
                        write_nc_output(
                            output_nc_file + "_cbf",
                            eof_lr_cbf,
                            cbf_pc,
                            frac_cbf,
                            slope_cbf,
                            intercept_cbf,
                        )

                    # Graphics -- plot map image to PNG
                    output_img_file = os.path.join(
                        dir_paths["graphics"], output_filename
                    )
                    if plot_model:
                        plot_map(
                            mode,
                            f"{mip.upper()} {model} ({run}) - CBF",
                            msyear,
                            meyear,
                            season,
                            model_timeseries_season_subdomain["eof_lr_cbf"],
                            frac_cbf,
                            output_img_file + "_cbf",
                            debug=debug,
                        )
                        plot_map(
                            mode + "_teleconnection",
                            f"{mip.upper()} {model} ({run}) - CBF",
                            msyear,
                            meyear,
                            season,
                            # eof_lr_cbf(longitude=(lon1_global, lon2_global)),
                            eof_lr_cbf,
                            frac_cbf,
                            output_img_file + "_cbf_teleconnection",
                            debug=debug,
                        )

                    debug_print("cbf pcs end", debug)

                # -------------------------------------------------
                # Conventional EOF approach as supplementary
                # - - - - - - - - - - - - - - - - - - - - - - - - -
                if ConvEOF:
                    eofn_mod_max = 3

                    # EOF analysis
                    debug_print("conventional EOF analysis start", debug)
                    (
                        eof_list,
                        pc_list,
                        frac_list,
                        reverse_sign_list,
                        solver,
                    ) = eof_analysis_get_variance_mode(
                        mode,
                        model_timeseries_season_subdomain,
                        var,
                        eofn=eofn_mod,
                        eofn_max=eofn_mod_max,
                        debug=debug,
                        EofScaling=EofScaling,
                        save_multiple_eofs=True,
                    )
                    debug_print("conventional EOF analysis done", debug)

                    # -------------------------------------------------
                    # For multiple EOFs (e.g., EOF1, EOF2, EOF3, ...)
                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    rms_list = []
                    cor_list = []
                    tcor_list = []

                    for n in range(0, eofn_mod_max):
                        eofs = "eof" + str(n + 1)
                        if (
                            eofs
                            not in result_dict["RESULTS"][model][run][
                                "defaultReference"
                            ][mode][season]
                        ):
                            result_dict["RESULTS"][model][run]["defaultReference"][
                                mode
                            ][season][eofs] = {}
                            dict_head = result_dict["RESULTS"][model][run][
                                "defaultReference"
                            ][mode][season][eofs]

                        # Component for each EOFs
                        eof = eof_list[n]
                        pc = pc_list[n]
                        frac = frac_list[n]

                        # Calculate stdv of pc time series
                        stdv_pc = calcSTD(pc)

                        # Linear regression to have extended global map:
                        (
                            eof_lr,
                            slope,
                            intercept,
                        ) = linear_regression_on_globe_for_teleconnection(
                            pc,
                            model_timeseries_season,
                            var,
                            stdv_pc,
                            RmDomainMean,
                            EofScaling,
                            debug=debug,
                        )

                        model_timeseries_season["eof_lr"] = eof_lr
                        model_timeseries_season["slope"] = slope
                        model_timeseries_season["intercept"] = intercept

                        # - - - - - - - - - - - - - - - - - - - - - - - - -
                        # Record results
                        # - - - - - - - - - - - - - - - - - - - - - - - - -
                        # Metrics results -- statistics to JSON
                        common_args = {
                            "mode": mode,
                            "dict_head": dict_head,
                            "model_ds": model_timeseries_season,
                            "model_data_var": "eof_lr",
                            "eof": eof,
                            "eof_lr": eof_lr,
                            "pc": pc,
                            "stdv_pc": stdv_pc,
                            "frac": frac,
                            "regions_specs": regions_specs,
                            "obs_compare": obs_compare,
                            "method": "eof",
                            "debug": debug,
                        }

                        if obs_compare:
                            common_args.update(
                                {
                                    "obs_ds": obs_timeseries_season_dict[season],
                                    "eof_obs": eof_obs[season],
                                    "eof_lr_obs": eof_lr_obs[season],
                                    "stdv_pc_obs": stdv_pc_obs[season],
                                }
                            )

                        dict_head, eof_lr = calc_stats_save_dict(**common_args)

                        # Temporal correlation between CBF PC timeseries and usual model PC timeseries
                        if CBF:
                            tc = calcTCOR(cbf_pc, pc)
                            debug_print("cbf tc end", debug)
                            dict_head["tcor_cbf_vs_eof_pc"] = tc

                        # Set output file name for NetCDF and plot images
                        output_filename = f"{mode}_{var}_EOF{n+1}_{season}_{mip}_{model}_{exp}_{run}_{fq}_{realm}_{msyear}-{meyear}"
                        if EofScaling:
                            output_filename += "_EOFscaled"

                        # Diagnostics results -- data to NetCDF
                        # Save global map, pc timeseries, and fraction in NetCDF output
                        output_nc_file = os.path.join(
                            dir_paths["diagnostic_results"], output_filename
                        )
                        if nc_out_model:
                            write_nc_output(
                                output_nc_file, eof_lr, pc, frac, slope, intercept
                            )

                        # Graphics -- plot map image to PNG
                        output_img_file = os.path.join(
                            dir_paths["graphics"], output_filename
                        )
                        if plot_model:
                            plot_map(
                                mode,
                                f"{mip.upper()} {model} ({run}) - EOF{n + 1}",
                                msyear,
                                meyear,
                                season,
                                # eof_lr(region_subdomain),
                                # region_subset(eof_lr, mode, regions_specs),
                                region_subset(
                                    model_timeseries_season,
                                    mode,
                                    data_var="eof_lr",
                                    regions_specs=regions_specs,
                                )["eof_lr"],
                                frac,
                                output_img_file,
                                debug=debug,
                            )
                            plot_map(
                                mode + "_teleconnection",
                                f"{mip.upper()} {model} ({run}) - EOF{n + 1}",
                                msyear,
                                meyear,
                                season,
                                # eof_lr(longitude=(lon1_global, lon2_global)),
                                eof_lr,
                                frac,
                                output_img_file + "_teleconnection",
                                debug=debug,
                            )

                        # - - - - - - - - - - - - - - - - - - - - - - - - -
                        # EOF swap diagnosis
                        # - - - - - - - - - - - - - - - - - - - - - - - - -
                        rms_list.append(dict_head["rms"])
                        cor_list.append(dict_head["cor"])
                        if CBF:
                            tcor_list.append(dict_head["tcor_cbf_vs_eof_pc"])

                    # Find best matching eofs with different criteria
                    best_matching_eofs_rms = rms_list.index(min(rms_list)) + 1
                    best_matching_eofs_cor = cor_list.index(max(cor_list)) + 1
                    if CBF:
                        best_matching_eofs_tcor = tcor_list.index(max(tcor_list)) + 1

                    # Save the best matching information to JSON
                    dict_head = result_dict["RESULTS"][model][run]["defaultReference"][
                        mode
                    ][season]
                    dict_head["best_matching_model_eofs__rms"] = best_matching_eofs_rms
                    dict_head["best_matching_model_eofs__cor"] = best_matching_eofs_cor
                    if CBF:
                        dict_head[
                            "best_matching_model_eofs__tcor_cbf_vs_eof_pc"
                        ] = best_matching_eofs_tcor

                    debug_print("conventional eof end", debug)

            # =================================================================
            # Dictionary to JSON: individual JSON during model_realization loop
            # -----------------------------------------------------------------
            json_filename_tmp = f"var_mode_{mode}_EOF{eofn_mod}_stat_{mip}_{exp}_{fq}_{realm}_{model}_{run}_{msyear}-{meyear}"

            variability_metrics_to_json(
                dir_paths["metrics_results"],
                json_filename_tmp,
                result_dict,
                model=model,
                run=run,
                cmec_flag=cmec,
            )
        """
        except Exception as err:
            if debug:
                raise
            else:
                print("warning: failed for ", model, run, err)
                pass
        """
# ========================================================================
# Dictionary to JSON: collective JSON at the end of model_realization loop
# ------------------------------------------------------------------------
if not parallel and (len(models) > 1):
    json_filename_all = f"var_mode_{mode}_EOF{eofn_mod}_stat_{mip}_{exp}_{fq}_{realm}_allModels_allRuns_{msyear}-{meyear}"
    variability_metrics_to_json(
        dir_paths["metrics_results"], json_filename_all, result_dict, cmec_flag=cmec
    )

if not debug:
    sys.exit(0)
