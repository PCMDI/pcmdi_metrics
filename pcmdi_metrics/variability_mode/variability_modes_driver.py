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
- PSA2: Pacific South America Mode (2nd EOFs of SAM domain)
- EA: East Atlantic Pattern (2nd EOF of NAO domain)

## EOF3 based variability modes
- PSA3: Pacific South America Mode (3rd EOFs of SAM domain)
- SCA: Scandinavian Pattern (3rd EOF of NAO domain)

## Reference:
Lee, J., K. Sperber, P. Gleckler, C. Bonfils, and K. Taylor, 2019:
Quantifying the Agreement Between Observed and Simulated Extratropical Modes of
Interannual Variability. Climate Dynamics.
https://doi.org/10.1007/s00382-018-4355-4
"""
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
    plot_map_multi_panel,
    read_data_in,
    search_paths,
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
provenance = param.provenance

print("EofScaling:", EofScaling)
print("RmDomainMean:", RmDomainMean)
print("LandMask:", LandMask)
print("provenance:", provenance)

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

# Initialize ref_grid_global
ref_grid_global = None

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
eofn_obs = param.eofn_obs
eofn_mod = param.eofn_mod
eofn_mod_max = param.eofn_mod_max

if mode in ["NAM", "NAO", "SAM", "PNA", "PDO", "AMO"]:
    eofn_expected = 1
elif mode in ["NPGO", "NPO", "PSA1", "EA"]:
    eofn_expected = 2
elif mode in ["PSA2", "SCA"]:
    eofn_expected = 3
else:
    print(
        f"Warning: Mode '{mode}' is not defined with an associated expected EOF number"
    )
    eofn_expected = None

if eofn_obs is None:
    eofn_obs = eofn_expected
else:
    eofn_obs = int(eofn_obs)
    if eofn_expected is not None:
        if eofn_obs != eofn_expected:
            print(
                f"Warning: Observation EOF number ({eofn_obs}) does not match expected EOF number ({eofn_expected}) for mode {mode}"
            )

if eofn_mod is None:
    eofn_mod = eofn_expected
else:
    eofn_mod = int(eofn_mod)
    if eofn_expected is not None:
        if eofn_mod != eofn_expected:
            print(
                f"Warning: Model EOF number ({eofn_mod}) does not match expected EOF number ({eofn_expected}) for mode {mode}"
            )

if eofn_expected is None:
    eofn_expected = eofn_mod

if eofn_mod_max is None:
    eofn_mod_max = eofn_mod

print("eofn_obs:", eofn_obs)
print("eofn_mod:", eofn_mod)
print("eofn_mod_max:", eofn_mod_max)

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
        with open(json_file) as fj:
            result_dict = json.load(fj)

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
        obs_var,
        var,
        osyear,
        oeyear,
        UnitsAdjust=ObsUnitsAdjust,
        lf_path=obs_lf_path,
        LandMask=LandMask,
        debug=debug,
    )

    # Get global grid information for later use: regrid
    if ref_grid_global is None:
        ref_grid_global = get_grid(obs_timeseries)

    # Set dictionary variables to keep information from observation in the memory during the season and model loop
    eof_obs = {}
    pc_obs = {}
    frac_obs = {}
    solver_obs = {}
    reverse_sign_obs = {}
    eof_lr_obs = {}
    eof_lr_obs_domain = {}
    stdv_pc_obs = {}
    obs_timeseries_season_dict = {}

    # Set dictonary for json archive
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

        if debug:
            print("obs_timeseries_season", obs_timeseries_season)

        # Extract subdomain
        obs_timeseries_season_subdomain = region_subset(
            obs_timeseries_season, mode, regions_specs
        )

        if debug:
            print("obs_timeseries_season_subdomain", obs_timeseries_season_subdomain)

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

        eof_lr_obs_domain[season] = obs_timeseries_season_region["eof_lr"]
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
                eof_lr_obs_domain[season],
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
                eof_lr_obs[season],
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
                eof_lr_obs_season,
                pc_obs[season],
                frac_obs[season],
                slope_obs,
                intercept_obs,
                identifier=obs_name,
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
        north_test_plot_title = f"{mode}, {season}, {obs_name} {osyear}-{oeyear}"
        north_test_output_filename = (
            f"EG_Spec_North_test_{mode}_{season}_{obs_name}_{osyear}-{oeyear}"
        )
        north_test(
            solver_obs[season],
            outdir=dir_paths["diagnostic_results"],
            output_filename=north_test_output_filename,
            plot_title=north_test_plot_title,
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

    debug_print(f"model_path_list: {model_path_list}", debug)

    # Find where run can be gripped from given filename template for modpath
    if "*" in realization:
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

        runs = [
            re.split("[._]", model_path.split("/")[-1])[run_in_modpath]
            for model_path in model_path_list
        ]

    else:
        if isinstance(realization, str):
            runs = [realization]
        elif isinstance(realization, list):
            runs = realization
        else:
            raise ValueError("realization must be a string or a list.")

    print("runs:", runs)

    # -------------------------------------------------
    # Run
    # -------------------------------------------------
    for run in runs:
        print("run:", runs)
        try:
            print(" --- ", run, " ---")

            model_run_path = search_paths(model_path_list, model, run)
            print("model_run_path:", model_run_path)

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
            print("model_lf_path:", model_lf_path)

            # read data in
            model_timeseries = read_data_in(
                model_run_path,
                var,
                var,
                msyear,
                meyear,
                UnitsAdjust=ModUnitsAdjust,
                lf_path=model_lf_path,
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
                    model_timeseries_season_regrid = regrid(
                        model_timeseries_season,
                        var,
                        ref_grid_global,
                        regrid_tool="regrid2",
                        fill_zero=True,
                    )

                    # QC
                    if var == "ts":
                        model_timeseries_season_regrid[
                            var
                        ] = model_timeseries_season_regrid[var].where(
                            model_timeseries_season_regrid[var] < 1e10
                        )

                    # crop to subdomain
                    model_timeseries_season_regrid_subdomain = region_subset(
                        model_timeseries_season_regrid, mode, regions_specs, debug=debug
                    )

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
                    model_timeseries_season_subdomain = region_subset(
                        model_timeseries_season,
                        mode,
                        regions_specs=regions_specs,
                    )

                    # Calculate fraction of variance explained by cbf pc
                    # (native grid)
                    frac_cbf = gain_pcs_fraction(
                        model_timeseries_season_subdomain,
                        var,
                        model_timeseries_season_subdomain,
                        "eof_lr_cbf",
                        cbf_pc / stdv_cbf_pc,
                        debug=debug,
                    )

                    # (regrid domain): sensitivity test purpose
                    frac_cbf_regrid = gain_pcs_fraction(
                        model_timeseries_season_regrid_subdomain,
                        var,
                        model_timeseries_season_subdomain,
                        "eof_lr_cbf",
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
                            identifier=f"{mip.upper()} {model} ({run}), CBF",
                        )

                    # Graphics -- plot map image to PNG
                    output_img_file = os.path.join(
                        dir_paths["graphics"], output_filename
                    )
                    if plot_model:
                        # Regional map
                        plot_map(
                            mode,
                            f"{mip.upper()} {model} ({run}) - CBF",
                            msyear,
                            meyear,
                            season,
                            model_timeseries_season_subdomain["eof_lr_cbf"],
                            frac_cbf,
                            output_file_name=f"{output_img_file}_cbf",
                            debug=debug,
                        )
                        debug_print(
                            f"plot CBF mode domain for {model} {run} completed", debug
                        )

                        # Global map
                        plot_map(
                            mode + "_teleconnection",
                            f"{mip.upper()} {model} ({run}) - CBF",
                            msyear,
                            meyear,
                            season,
                            eof_lr_cbf,
                            frac_cbf,
                            output_file_name=f"{output_img_file}_cbf_teleconnection",
                            debug=debug,
                        )
                        debug_print(
                            f"plot CBF teleconnection for {model} {run} completed",
                            debug,
                        )

                        # Compare with observation
                        plot_map_multi_panel(
                            mode,
                            f"{mip.upper()} {model} ({run}) - CBF",
                            msyear,
                            meyear,
                            season,
                            eof_lr_obs_domain[season],  #  obs mode domain
                            eof_lr_obs[season],  # obs global
                            pc_obs[season],  # obs pc
                            model_timeseries_season_subdomain[
                                "eof_lr_cbf"
                            ],  # model mode domain
                            eof_lr_cbf,  # model global
                            cbf_pc,  # model pc
                            frac_cbf,
                            ref_name=obs_name,
                            output_file_name=f"{output_img_file}_cbf_compare_obs",
                            debug=debug,
                        )
                        debug_print(
                            f"plot CBF multiplot for {model} {run} completed", debug
                        )
                    debug_print("cbf pcs end", debug)

                # -------------------------------------------------
                # Conventional EOF approach as supplementary
                # - - - - - - - - - - - - - - - - - - - - - - - - -
                if ConvEOF:
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
                        eofs = f"eof{str(n + 1)}"
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
                                output_nc_file,
                                eof_lr,
                                pc,
                                frac,
                                slope,
                                intercept,
                                identifier=f"{mip.upper()} {model} ({run}), {eofs.upper()}",
                            )

                        # Graphics -- plot map image to PNG
                        output_img_file = os.path.join(
                            dir_paths["graphics"], output_filename
                        )

                        eof_lr_domain = region_subset(
                            model_timeseries_season,
                            mode,
                            data_var="eof_lr",
                            regions_specs=regions_specs,
                        )["eof_lr"]

                        if plot_model:
                            # Regional map
                            plot_map(
                                mode,
                                f"{mip.upper()} {model} ({run}) - EOF{n + 1}",
                                msyear,
                                meyear,
                                season,
                                eof_lr_domain,
                                frac,
                                output_img_file,
                                debug=debug,
                            )
                            # Global map
                            plot_map(
                                f"{mode}_teleconnection",
                                f"{mip.upper()} {model} ({run}) - EOF{n + 1}",
                                msyear,
                                meyear,
                                season,
                                eof_lr,
                                frac,
                                f"{output_img_file}_teleconnection",
                                debug=debug,
                            )

                            if n + 1 == eofn_expected:
                                # Compare with observation
                                plot_map_multi_panel(
                                    mode,
                                    f"{mip.upper()} {model} ({run}) - EOF{n + 1}",
                                    msyear,
                                    meyear,
                                    season,
                                    eof_lr_obs_domain[season],  #  obs mode domain
                                    eof_lr_obs[season],  # obs global
                                    pc_obs[season],  # obs pc
                                    eof_lr_domain,  # model mode domain
                                    eof_lr,  # model global
                                    pc,  # model pc
                                    frac,
                                    ref_name=obs_name,
                                    output_file_name=f"{output_img_file}_eof{n+1}_compare_obs",
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
            debug_print("json (individual) writing start", debug)
            json_filename_tmp = f"var_mode_{mode}_EOF{eofn_mod}_stat_{mip}_{exp}_{fq}_{realm}_{model}_{run}_{msyear}-{meyear}"

            variability_metrics_to_json(
                dir_paths["metrics_results"],
                json_filename_tmp,
                result_dict,
                model=model,
                run=run,
                cmec_flag=cmec,
                include_provenance=provenance,
            )
            debug_print("json (individual) writing done", debug)

        except Exception as err:
            if debug:
                raise
            else:
                print("warning: metrics calculation failed for ", model, run, err)

# ========================================================================
# Dictionary to JSON: collective JSON at the end of model_realization loop
# ------------------------------------------------------------------------
if not parallel and (len(models) > 1):
    debug_print("json (collective) writing start", debug)
    json_filename_all = f"var_mode_{mode}_EOF{eofn_mod}_stat_{mip}_{exp}_{fq}_{realm}_allModels_allRuns_{msyear}-{meyear}"
    variability_metrics_to_json(
        dir_paths["metrics_results"], json_filename_all, result_dict, cmec_flag=cmec
    )
    debug_print("json (collective) writing done", debug)

if not debug:
    sys.exit(0)
