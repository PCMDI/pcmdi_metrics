# ---------------------------------------------------#
# Aim of the program:
#      plot portraitplots based on json files outputs of the CLIVAR ENSO metrics package
# ---------------------------------------------------#

# ---------------------------------------------------#
# Import the right packages
# ---------------------------------------------------#
import difflib
import json
import string
from copy import deepcopy

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
from numpy import linspace as NUMPYlinspace
from numpy import mean as NUMPYmean
from numpy import std as NUMPYstd
from numpy.ma import array as NUMPYma__array
from numpy.ma import masked_invalid as NUMPYma__masked_invalid
from numpy.ma import masked_where as NUMPYmasked_where
from numpy.ma import zeros as NUMPYma__zeros

# ENSO_metrics functions
from .EnsoPlotLib import plot_param

# ---------------------------------------------------#
# Main
# ---------------------------------------------------#


def enso_portrait_plot(
    metric_collections,
    list_project,
    list_obs,
    dict_json_path,
    figure_name="enso_portrait_plot.png",
    reduced_set=False,
    met_order=None,
    mod_order=None,
    sort_y_names=False,
    show_proj_means=False,
    show_ref_row=False,
    show_alt_obs_rows=False,
):
    """
    Generates a summary plot for ENSO metrics.

    Parameters
    ----------
    metric_collections : list of str
        List of metric collections to be plotted.
    list_project : list of str
        List of project names.
    list_obs : list of str
        List of observational datasets.
    dict_json_path : dict
        Dictionary containing paths to JSON files with metric data.
    figure_name : str, optional
        Name of the output figure file, by default "enso_portrait_plot.png".
    reduced_set : bool, optional
        If True, use a reduced set of metrics, by default False.
    met_order : list of str, optional
        Custom order for metrics, by default None.
    mod_order : list of str, optional
        Custom order for models, by default None.
    sort_y_names : bool, optional
        If True, sort y-axis names in alphabetical order, by default False.
    show_proj_means : bool, optional
        If True, show project means, by default False.
    show_ref_row : bool, optional
        If True, show reference row, by default False.
    show_alt_obs_rows : bool, optional
        If True, show alternative observation rows, by default False.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The generated figure.
    ref_info_dict : dict
        Dictionary containing reference information.
    """
    # name of metric collections for the plot and new metric names
    metric_names_for_plot, met_names = load_met_names()

    # metric type and order
    if met_order is None:
        met_order, met_o1, met_o2, met_o3, met_o4 = load_met_order()

    # model order
    if mod_order == "predefined":
        mod_order = predefined_mod_order()

    # list of observations
    if list_obs is None:
        list_obs = list()

    # get data
    tab_all, x_names, y_names, ref_info_dict = json_dict_to_numpy_array_list(
        metric_collections,
        list_project,
        list_obs,
        dict_json_path,
        reduced_set,
        met_order,
        mod_order,
        sort_y_names=sort_y_names,
        show_proj_means=show_proj_means,
        show_ref_row=show_ref_row,
        show_alt_obs_rows=show_alt_obs_rows,
    )

    # all portraitplots in one plot
    numbering = [ii + ") " for ii in list(string.ascii_lowercase)]

    # plot
    title = [
        numbering[ii] + metric_names_for_plot[mc]
        for ii, mc in enumerate(metric_collections)
    ]

    if "CMIP6" in list_project and "CMIP5" in list_project:
        text = "* = CMIP6\nmodel"
    else:
        text = None

    levels = list(range(-2, 3))
    fig = multiportraitplot(
        tab_all,
        figure_name,
        x_names,
        y_names,
        title=title,
        my_text=text,
        levels=levels,
        highlight=True,
        met_o1=met_o1,
        met_o2=met_o2,
        met_o3=met_o3,
        met_o4=met_o4,
        met_names=met_names,
    )
    del levels, numbering, text, title
    return fig, ref_info_dict


# ---------------------------------------------------#
# Support Functions
# ---------------------------------------------------#
def json_dict_to_numpy_array_list(
    metric_collections,
    list_project,
    list_obs,
    dict_json_path,
    reduced_set,
    met_order,
    mod_order,
    sort_y_names=False,
    show_proj_means=False,
    show_ref_row=False,
    show_alt_obs_rows=False,
    debug=False,
):
    if debug:
        print("metric_collections:", metric_collections)
        print("list_project:", list_project)
        print("list_obs:", list_obs)
    # get members by model by project from json file
    # only metrics from models/members chosen here will be used
    # all metrics from models/members chosen here will be used (ensures that if a model/member is not available for one or
    # several metric collections, the corresponding line will still be created in the portraitplot)
    model_by_proj = dict()
    dict_members = dict()
    for proj in list_project:
        list_models = list()
        dict_members[proj] = dict()
        for mc in metric_collections:
            # read json files
            tmp = read_data(dict_json_path[proj][mc])
            # list models
            list_models += list(tmp.keys())
            # members
            for mod in list(tmp.keys()):
                try:
                    dict_members[proj][mod]
                except KeyError:
                    dict_members[proj][mod] = list(tmp[mod].keys())
                else:
                    dict_members[proj][mod] += list(tmp[mod].keys())
            del tmp
        list_models = sorted(list(set(list_models)), key=lambda v: v.upper())
        list_to_remove = None
        list_to_remove = [
            "EC-EARTH",
            "FIO-ESM",
            "GFDL-CM2p1",
            "HadGEM2-AO",
            "CIESM",
            "E3SM-1-1-ECA",
            "FGOALS-g3",
            "MCM-UA-1-0",
            "AWI-CM-1-1-MR",
            "AWI-ESM-1-1-LR",
        ]
        # EC-EARTH: incorrect time coordinate
        # FIO-ESM, HadCM3: grid issues
        # GFDL-CM2p1: hfls not published
        # HadGEM2-AO: rlus and rsus not published
        # E3SM-1-1-ECA: Experimental stage
        # CIESM, FGOALS-g3: ???
        # MCM-UA-1-0: unit issue with pr
        # AWI-CM-1-1-MR, AWI-ESM-1-1-LR: error at ENSO_proc calculation
        if list_to_remove is not None:
            for mod in list_to_remove:
                while mod in list_models:
                    list_models.remove(mod)
        for mod in list_models:
            list_members = sorted(
                list(set(dict_members[proj][mod])), key=lambda v: v.upper()
            )
            mem = find_first_member(list_members, mod=mod)
            try:
                model_by_proj[proj]
            except KeyError:
                model_by_proj[proj] = {mod: mem}
            else:
                try:
                    model_by_proj[proj][mod]
                except KeyError:
                    model_by_proj[proj][mod] = mem
                else:
                    print("this model should not be here")
            del list_members, mem
        # del dict_members, list_models, list_to_remove
        del list_models, list_to_remove

    # read json file
    tab_all, tab_all_act, x_names = list(), list(), list()
    different_ref_keys = list()
    ref_info_dict = dict()

    for mc in metric_collections:
        if debug:
            print("mc:", mc)
        dict1 = dict()
        list_models_all = list()
        ref_info_dict[mc] = dict()
        for proj in list_project:
            ref_info_dict[mc][proj] = dict()
            # open and read json file
            data_json = read_data(dict_json_path[proj][mc])
            # read metrics
            list_models = sorted(
                list(model_by_proj[proj].keys()), key=lambda v: v.upper()
            )
            list_models_all.extend(list_models)
            for mod in list_models:
                data_mod = data_json[mod][model_by_proj[proj][mod]]["value"]
                list_metrics = sorted(list(data_mod.keys()), key=lambda v: v.upper())
                if reduced_set is True:
                    list_metrics = remove_metrics(list_metrics, mc)
                for met in list_metrics:
                    ref = get_reference(mc, met)  # e.g., 'GPCPv2.3'
                    ref_key_list = list(
                        data_mod[met]["metric"]
                    )  # e.g., ['GPCP-2-3', and others]
                    ref_key_act = most_similar_string(ref, ref_key_list)
                    if ref != ref_key_act:
                        if debug:
                            print(
                                f"Note: For metrics collection '{mc}' metric '{met}', reference key in the JSON for the project '{proj}', '{ref_key_act}', is assumed to be same as the predefined reference, '{ref}'."
                            )
                        different_ref_keys.append([ref, ref_key_act])

                    ref_info_dict[mc][proj][met] = ref_key_act
                    # val = data_mod[met]["metric"][ref]["value"]
                    # Below, if any part of the dictionary chain is missing, val will be set to None without raising a KeyError.
                    val = (
                        data_mod.get(met, {})
                        .get("metric", {})
                        .get(ref_key_act, {})
                        .get("value", None)
                    )
                    if val is None:
                        val = 1e20
                    try:
                        dict1[mod]
                    except KeyError:
                        dict1[mod] = {met: val}
                    else:
                        dict1[mod][met] = val
                    del ref, ref_key_act, val
                del data_mod, list_metrics
            del data_json, list_models

        if len(different_ref_keys) > 0:
            print(
                f"Note: The following keys were considered to be the same for {proj}:"
            )
            unique_different_ref_keys = list(
                map(list, dict.fromkeys(map(tuple, different_ref_keys)))
            )
            for diff_keys in unique_different_ref_keys:
                print(
                    f"Predefined reference: {diff_keys[0]}, reference key in the JSON: {diff_keys[1]}"
                )

        # models and metrics
        if sort_y_names:
            tmp_models = sorted(
                [str(mod) for mod in list(dict1.keys())], key=lambda v: v.upper()
            )
        else:
            tmp_models = list_models_all

        if debug:
            print("tmp_models:", tmp_models)

        my_metrics = list()
        for mod in tmp_models:
            try:
                list(dict1[mod].keys())
            except KeyError:
                pass
            else:
                my_metrics += list(dict1[mod].keys())

        my_metrics = sorted(list(set(my_metrics)), key=lambda v: v.upper())

        if met_order is not None:
            my_metrics = [met for met in met_order if met in my_metrics]

        if mod_order is not None:
            my_models = [mod for mod in mod_order if mod in tmp_models]
        else:
            my_models = tmp_models
        my_models += sorted(
            list(set(tmp_models) - set(my_models)), key=lambda v: v.upper()
        )
        my_models = list(reversed(my_models))
        del tmp_models

        if debug:
            print("my_models:", my_models)

        # Additional rows (project multi-model means (e.g., CMIP mean), reference, and alternative observation datasets)
        rows_to_add = list()
        dict_ref_met = dict()

        if show_alt_obs_rows and list_obs is not None:
            rows_to_add += list_obs

            if len(list_obs) > 0 and "obs2obs" in dict_json_path.keys():
                # read other observational datasets compared to the reference
                dict_ref_met = read_obs(
                    dict_json_path["obs2obs"][mc], list_obs, my_metrics, mc
                )

        if show_ref_row:
            rows_to_add += ["reference"]

        if show_proj_means:
            rows_to_add += list(reversed(list_project))

        plus = len(rows_to_add)

        if debug:
            print("rows_to_add:", rows_to_add)
            print("plus:", plus)

        # fill array
        tab = NUMPYma__zeros((len(my_models) + plus, len(my_metrics)))
        if debug:
            print("tab.shape:", tab.shape)

        for ii, mod in enumerate(my_models):
            for jj, met in enumerate(my_metrics):
                try:
                    dict1[mod][met]
                except KeyError:
                    tab[ii + plus, jj] = 1e20
                else:
                    tab[ii + plus, jj] = dict1[mod][met]
        tab = NUMPYma__masked_invalid(tab)
        tab = NUMPYmasked_where(tab == 1e20, tab)
        tab_act = deepcopy(tab)

        # add values to the array (CMIP mean, reference, other observational datasets,...)
        for jj, met in enumerate(my_metrics):
            tmp = tab[plus:, jj].compressed()
            mea = float(NUMPYmean(tmp))
            std = float(NUMPYstd(tmp))
            del tmp
            for ii, dd in enumerate(rows_to_add):
                if dd in list_obs:
                    # Get value from dict_ref_met for alternative observations in list_obs
                    val = dict_ref_met[dd][met]
                elif dd in list_project:
                    # Get average value of models for the project
                    tmp = [
                        tab[ii + plus, jj]
                        for ii, mod in enumerate(my_models)
                        if mod in list(model_by_proj[dd].keys())
                    ]
                    tmp = NUMPYma__masked_invalid(NUMPYma__array(tmp))
                    tmp = NUMPYmasked_where(tmp == 1e20, tmp).compressed()
                    val = float(NUMPYmean(tmp))
                    del tmp
                else:
                    # For the default reference
                    val = 0
                tab[ii, jj] = val
                tab_act[ii, jj] = val
                del val
            # normalize
            tab[:, jj] = (tab[:, jj] - mea) / std
            del mea, std
        tab = NUMPYma__masked_invalid(tab)
        tab = NUMPYmasked_where(tab > 1e3, tab)
        tab_act = NUMPYma__masked_invalid(tab_act)
        tab_act = NUMPYmasked_where(tab_act > 1e3, tab_act)
        tab_all.append(tab)
        tab_all_act.append(tab_act)

        if reduced_set is True:
            x_names.append(
                [met.replace("_1", "").replace("_2", "") for met in my_metrics]
            )
        else:
            x_names.append(my_metrics)

        if "CMIP6" in list_project and "CMIP5" in list_project:
            my_models = [
                "* " + mod if mod in list(model_by_proj["CMIP6"].keys()) else mod
                for mod in my_models
            ]

        if mc == metric_collections[0]:
            y_names = rows_to_add + my_models
            y_names = [
                "(" + dd + ")" if dd in (list_obs + ["reference"]) else dd
                for dd in y_names
            ]
        del dict1, dict_ref_met, my_metrics, my_models, plus, tab, tab_act

    if debug:
        print("len(tab_all):", len(tab_all))

    return tab_all, x_names, y_names, ref_info_dict


def most_similar_string(target, string_list):
    return max(
        string_list, key=lambda s: difflib.SequenceMatcher(None, target, s).ratio()
    )


def load_met_names():
    # name of metric collections for the plot
    metric_names_for_plot = {
        "ENSO_perf": "Performance",
        "ENSO_proc": "Processes",
        "ENSO_tel": "Telecon.",
    }

    # new metric names
    met_names = {
        "BiasPrLatRmse": "double_ITCZ_bias",
        "BiasPrLonRmse": "eq_PR_bias",
        "BiasSstLonRmse": "eq_SST_bias",
        "BiasTauxLonRmse": "eq_Taux_bias",
        "SeasonalPrLatRmse": "double_ITCZ_sea_cycle",
        "SeasonalPrLonRmse": "eq_PR_sea_cycle",
        "SeasonalSstLonRmse": "eq_SST_sea_cycle",
        "SeasonalTauxLonRmse": "eq_Taux_sea_cycle",
        "EnsoSstLonRmse": "ENSO_pattern",
        "EnsoSstTsRmse": "ENSO_lifecycle",
        "EnsoAmpl": "ENSO_amplitude",
        "EnsoSeasonality": "ENSO_seasonality",
        "EnsoSstSkew": "ENSO_asymmetry",
        "EnsoDuration": "ENSO_duration",
        "EnsoSstDiversity": "ENSO_diversity",
        "EnsoSstDiversity_1": "ENSO_diversity",
        "EnsoSstDiversity_2": "ENSO_diversity",
        "EnsoPrMapDjfRmse": "DJF_PR_teleconnection",
        "EnsoPrMapJjaRmse": "JJA_PR_teleconnection",
        "EnsoSstMapDjfRmse": "DJF_TS_teleconnection",
        "EnsoSstMapJjaRmse": "JJA_TS_teleconnection",
        "EnsoFbSstTaux": "SST-Taux_feedback",
        "EnsoFbTauxSsh": "Taux-SSH_feedback",
        "EnsoFbSshSst": "SSH-SST_feedback",
        "EnsoFbSstThf": "SST-NHF_feedback",
        "EnsodSstOce": "ocean_driven_SST",
        "EnsodSstOce_1": "ocean_driven_SST",
        "EnsodSstOce_2": "ocean_driven_SST",
    }

    return metric_names_for_plot, met_names


def load_met_order():
    # metric type and order
    met_o1 = [
        "BiasPrLatRmse",
        "BiasPrLonRmse",
        "BiasSshLatRmse",
        "BiasSshLonRmse",
        "BiasSstLatRmse",
        "BiasSstLonRmse",
        "BiasTauxLatRmse",
        "BiasTauxLonRmse",
        "SeasonalPrLatRmse",
        "SeasonalPrLonRmse",
        "SeasonalSshLatRmse",
        "SeasonalSshLonRmse",
        "SeasonalSstLatRmse",
        "SeasonalSstLonRmse",
        "SeasonalTauxLatRmse",
        "SeasonalTauxLonRmse",
    ]
    met_o2 = [
        "EnsoSstLonRmse",
        "EnsoPrTsRmse",
        "EnsoSstTsRmse",
        "EnsoTauxTsRmse",
        "EnsoAmpl",
        "EnsoSeasonality",
        "EnsoSstSkew",
        "EnsoDuration",
        "EnsoSstDiversity",
        "EnsoSstDiversity_1",
        "EnsoSstDiversity_2",
        "NinoSstDiversity",
        "NinoSstDiversity_1",
        "NinoSstDiversity_2",
    ]
    met_o3 = [
        "EnsoPrMapCorr",
        "EnsoPrMapRmse",
        "EnsoPrMapStd",
        "EnsoPrMapDjfCorr",
        "EnsoPrMapDjfRmse",
        "EnsoPrMapDjfStd",
        "EnsoPrMapJjaCorr",
        "EnsoPrMapJjaRmse",
        "EnsoPrMapJjaStd",
        "EnsoSlpMapCorr",
        "EnsoSlpMapRmse",
        "EnsoSlpMapStd",
        "EnsoSlpMapDjfCorr",
        "EnsoSlpMapDjfRmse",
        "EnsoSlpMapDjfStd",
        "EnsoSlpMapJjaCorr",
        "EnsoSlpMapJjaRmse",
        "EnsoSlpMapJjaStd",
        "EnsoSstMapCorr",
        "EnsoSstMapRmse",
        "EnsoSstMapStd",
        "EnsoSstMapDjfCorr",
        "EnsoSstMapDjfRmse",
        "EnsoSstMapDjfStd",
        "EnsoSstMapJjaCorr",
        "EnsoSstMapJjaRmse",
        "EnsoSstMapJjaStd",
    ]
    met_o4 = [
        "EnsoFbSstTaux",
        "EnsoFbTauxSsh",
        "EnsoFbSshSst",
        "EnsoFbSstThf",
        "EnsoFbSstSwr",
        "EnsoFbSstLhf",
        "EnsoFbSstLwr",
        "EnsoFbSstShf",
        "EnsodSstOce",
        "EnsodSstOce_1",
        "EnsodSstOce_2",
    ]
    met_order = met_o1 + met_o2 + met_o3 + met_o4

    return met_order, met_o1, met_o2, met_o3, met_o4


def predefined_mod_order():
    # model order
    mod_order = [
        "ACCESS1-0",
        "ACCESS1-3",
        "ACCESS-CM2",
        "ACCESS-ESM1-5",
        "BCC-CSM1-1",
        "BCC-CSM1-1-M",
        "BCC-CSM2-MR",
        "BCC-ESM1",
        "BNU-ESM",
        "CAMS-CSM1-0",
        "CanCM4",
        "CanESM2",
        "CanESM5",
        "CanESM5-CanOE",
        "CCSM4",
        "CESM1-BGC",
        "CESM1-CAM5",
        "CESM2",
        "CESM2-FV2",
        "CESM1-FASTCHEM",
        "CESM1-WACCM",
        "CESM2-WACCM",
        "CESM2-WACCM-FV2",
        "CMCC-CESM",
        "CMCC-CM",
        "CMCC-CMS",
        "CNRM-CM5",
        "CNRM-CM5-2",
        "CNRM-CM6-1",
        "CNRM-CM6-1-HR",
        "CNRM-ESM2-1",
        "CSIRO-Mk3-6-0",
        "CSIRO-Mk3L-1-2",
        "E3SM-1-0",
        "E3SM-1-1",
        "EC-EARTH",
        "EC-Earth3",
        "EC-Earth3-Veg",
        "FGOALS-f3-L",
        "FGOALS-g2",
        "FGOALS-s2",
        "FIO-ESM",
        "GFDL-CM2p1",
        "GFDL-CM3",
        "GFDL-CM4",
        "GFDL-ESM2G",
        "GFDL-ESM2M",
        "GFDL-ESM4",
        "GISS-E2-1-G",
        "GISS-E2-1-G-CC",
        "GISS-E2-H",
        "GISS-E2-H-CC",
        "GISS-E2-1-H",
        "GISS-E2-R",
        "GISS-E2-R-CC",
        "HadCM3",
        "HadGEM2-AO",
        "HadGEM2-CC",
        "HadGEM2-ES",
        "HadGEM3-GC31-LL",
        "INMCM4",
        "INM-CM4-8",
        "INM-CM5-0",
        "IPSL-CM5A-LR",
        "IPSL-CM5A-MR",
        "IPSL-CM5B-LR",
        "IPSL-CM6A-LR",
        "KACE-1-0-G",
        "MIROC4h",
        "MIROC5",
        "MIROC6",
        "MIROC-ESM",
        "MIROC-ESM-CHEM",
        "MIROC-ES2L",
        "MPI-ESM-LR",
        "MPI-ESM-MR",
        "MPI-ESM-P",
        "MPI-ESM-1-2-HAM",
        "MPI-ESM1-2-HR",
        "MPI-ESM1-2-LR",
        "MRI-CGCM3",
        "MRI-ESM1",
        "MRI-ESM2-0",
        "NESM3",
        "NorESM1-M",
        "NorESM1-ME",
        "NorCPM1",
        "NorESM2-LM",
        "NorESM2-MM",
        "SAM0-UNICON",
        "TaiESM1",
        "UKESM1-0-LL",
    ]

    mod_order += [
        "CAS-ESM2-0",
        "CMCC-CM2-HR4",
        "CMCC-CM2-SR5",
        "EC-Earth3-AerChem",
        "EC-Earth3-Veg-LR",
        "FIO-ESM-2-0",
        "HadGEM3-GC31-MM",
        "KIOST-ESM",
    ]

    mod_order = sorted(mod_order, key=str.casefold)

    return mod_order


def find_first_member(members, mod=None):
    """
    Finds the first member

    Inputs:
    ------
    :param members: list of string
        List of members.

    Output:
    ------
    :return mem: string
        First member of the given list.
    """
    if "r1i1p1" in members:
        mem = "r1i1p1"
    elif "r1i1p1f1" in members:
        mem = "r1i1p1f1"
    elif "r1i1p1f2" in members:
        mem = "r1i1p1f2"
    else:
        tmp = deepcopy(members)
        members = list()
        for mem in tmp:
            for ii in range(1, 10):
                if "r" + str(ii) + "i" in mem:
                    members.append(
                        mem.replace("r" + str(ii) + "i", "r" + str(ii).zfill(2) + "i")
                    )
                else:
                    members.append(mem)
        del tmp
        mem = sorted(list(set(members)), key=lambda v: v.upper())[0].replace("r0", "r")
    # special case
    if mod == "NorESM2-LM":
        mem = "r2i1p1f1"
    return mem


def get_reference(metric_collection, metric):
    """
    Gets main reference for the given metric_collection / metric from EnsoPlotLib.plot_param

    Inputs:
    ------
    :param metric_collection: string
        Name of a metric collection.
    :param metric: string
        Name of a metric.

    Output:
    ------
    :return reference: string
        Name of the main reference for the given metric_collection / metric
    """
    if metric_collection in ["ENSO_tel", "test_tel"] and "Map" in metric:
        my_met = metric.replace("Corr", "").replace("Rmse", "").replace("Std", "")
    else:
        my_met = deepcopy(metric)
    reference = plot_param(metric_collection, my_met)["metric_reference"]
    return reference


def my_colorbar(mini=-1.0, maxi=1.0, nbins=20):
    """
    Modifies cmo.balance colobar (removes the darkest blue and red)

    Inputs:
    ------
    **Optional arguments:**
    :param mini: float
        Minimum value of the colorbar.
    :param maxi: float
        Maximum value of the colorbar.
    :param nbins: integer
        Number of interval in the colorbar.

    Outputs:
    -------
    :return newcmp1: object
        Colormap, baseclass for all scalar to RGBA mappings
    :return norm: object
        Normalize, a class which can normalize data into the [0.0, 1.0] interval.
    """
    levels = MaxNLocator(nbins=nbins).tick_values(mini, maxi)
    # cmap = plt.get_cmap("cmo.balance")
    cmap = plt.get_cmap("RdBu_r")
    newcmp1 = cmap(NUMPYlinspace(0.15, 0.85, 256))
    newcmp2 = cmap(NUMPYlinspace(0.0, 1.0, 256))
    newcmp1 = ListedColormap(newcmp1)
    newcmp1.set_over(newcmp2[-30])
    newcmp1.set_under(newcmp2[29])
    newcmp1.set_bad(color="k")  # missing values in black
    norm = BoundaryNorm(levels, ncolors=newcmp1.N)
    return newcmp1, norm


def multiportraitplot(
    tab,
    name_plot,
    x_names,
    y_names,
    title=[],
    write_metrics=False,
    my_text="",
    levels=None,
    highlight=False,
    nbr_space=2,
    met_o1=None,
    met_o2=None,
    met_o3=None,
    met_o4=None,
    met_names=None,
):
    """
    Plot the portraitplot (as in BAMS paper)

    Inputs:
    ------
    :param tab: list of masked_array
        List of masked_array containing metric collections values.
    :param name_plot: string
        Name of the output figure.
    :param x_names: list of list of string
        List of metric collection's metric names.
    :param y_names: list of string
        List of model/member names.
    **Optional arguments:**
    :param title: list of string, optional
        List of metric collection's title.
    :param my_text: string, optional
        Text to add at the bottom right of the plot (I use it to indicate how CMIP6 models are marked in the plot).
    :param levels: list of floats, optional
        Levels of the colorbar, if None is given, colobar ranges from -1 to 1.
    :param highlight: boolean, optional
        If True metric names are highlighted and lines indicate metric types.

    Output:
    ------
    """
    if levels is None:
        levels = [-1.0, -0.5, 0.0, 0.5, 1.0]
    fontdict = {"fontsize": 40, "fontweight": "bold"}
    # nbr of columns of the portraitplot
    nbrc = sum([len(tab[ii][0]) for ii in range(len(tab))]) + (len(tab) - 1) * nbr_space
    # figure definition
    fig = plt.figure(0, figsize=(0.5 * nbrc, 0.5 * len(tab[0])))
    gs = GridSpec(1, nbrc)
    # adapt the colorbar
    cmap, norm = my_colorbar(mini=min(levels), maxi=max(levels))
    # loop on metric collections
    count = 0
    for kk, tmp in enumerate(tab):
        ax = plt.subplot(gs[0, count : count + len(tmp[0])])
        # shading
        cs = ax.pcolormesh(tmp, cmap=cmap, norm=norm)
        # title
        xx1, xx2 = ax.get_xlim()
        dx = 0.5 / (xx2 - xx1)
        yy1, yy2 = ax.get_ylim()
        dy = 0.5 / (yy2 - yy1)
        try:
            ax.set_title(title[kk], fontdict=fontdict, y=1 + dy, loc="center")
        except Exception as e:
            print(f"An error occurred: {e}")
        # x axis
        ticks = [ii + 0.5 for ii in range(len(x_names[kk]))]
        ax.set_xticks(ticks)
        ax.set_xticklabels([] * len(ticks))
        for ll, txt in enumerate(x_names[kk]):
            if highlight is True:
                # find the metric color
                if txt in met_o1 or txt + "_1" in met_o1 or txt + "_2" in met_o1:
                    cc = "yellowgreen"
                elif txt in met_o2 or txt + "_1" in met_o2 or txt + "_2" in met_o2:
                    cc = "plum"
                elif txt in met_o3 or txt + "_1" in met_o3 or txt + "_2" in met_o3:
                    cc = "gold"
                else:
                    cc = "turquoise"
                # write highlighted metric name
                ax.text(
                    ll + 0.5,
                    -0.2,
                    met_names[txt],
                    fontsize=15,
                    ha="right",
                    va="top",
                    rotation=45,
                    color="k",
                    bbox=dict(lw=0, facecolor=cc, pad=3, alpha=1),
                )
            else:
                # write metric name in black
                ax.text(
                    ll + 0.5,
                    -0.2,
                    met_names[txt],
                    fontsize=20,
                    ha="right",
                    va="top",
                    rotation=45,
                    color="k",
                )
        if highlight is True:
            tmp1 = [met_o1, met_o2, met_o3, met_o4]
            # draw vertical black lines to separate metric types
            nn = 0
            lix = [[0, 0]]
            for tt in tmp1:
                tmp2 = [
                    txt
                    for ll, txt in enumerate(x_names[kk])
                    if txt in tt or txt + "_1" in tt or txt + "_2" in tt
                ]
                nn += len(tmp2)
                if len(tmp2) > 0:
                    lix += [[nn, nn]]
                del tmp2
            liy = [[0, len(tab[0])]] * len(lix)
            lic, lis = ["k"] * len(lix), ["-"] * len(lix)
            for lc, ls, lx, ly in zip(lic, lis, lix, liy):
                line = Line2D(lx, ly, c=lc, lw=7, ls=ls, zorder=10)
                line.set_clip_on(False)
                ax.add_line(line)
            # draw horizontal colored lines to indicate metric types
            nn = 0
            lic, lix = list(), list()
            for uu, tt in enumerate(tmp1):
                tmp2 = [
                    txt
                    for ll, txt in enumerate(x_names[kk])
                    if txt in tt or txt + "_1" in tt or txt + "_2" in tt
                ]
                if len(tmp2) > 0:
                    if uu == 0:
                        cc = "yellowgreen"
                    elif uu == 1:
                        cc = "plum"
                    elif uu == 2:
                        cc = "gold"
                    else:
                        cc = "turquoise"
                    lic += [cc, cc]
                    if nn > 0:
                        lix += [[nn + 0.2, nn + len(tmp2)], [nn + 0.2, nn + len(tmp2)]]
                    else:
                        lix += [[nn, nn + len(tmp2)], [nn, nn + len(tmp2)]]
                    nn += len(tmp2)
                    del cc
                del tmp2
            liy = [[len(tab[0]), len(tab[0])], [0, 0]] * int(float(len(lix)) / 2)
            lis = ["-"] * len(lix)
            for mm, (lc, ls, lx, ly) in enumerate(zip(lic, lis, lix, liy)):
                if mm < 2:
                    line = Line2D(
                        [lx[0] + 0.05, lx[1]], ly, c=lc, lw=10, ls=ls, zorder=10
                    )
                elif mm > len(lis) - 3:
                    line = Line2D(
                        [lx[0], lx[1] - 0.05], ly, c=lc, lw=10, ls=ls, zorder=10
                    )
                else:
                    line = Line2D(lx, ly, c=lc, lw=10, ls=ls, zorder=10)
                line.set_clip_on(False)
                ax.add_line(line)
        # y axis
        ticks = [ii + 0.5 for ii in range(len(y_names))]
        ax.set_yticks(ticks)
        if kk != 0:
            ax.set_yticklabels([""] * len(ticks))
        else:
            ax.text(
                -5 * dx,
                -1 * dy,
                my_text,
                fontsize=25,
                ha="right",
                va="top",
                transform=ax.transAxes,
            )
            ax.tick_params(axis="y", labelsize=20)
            ax.set_yticklabels(y_names)
        ax.yaxis.set_label_coords(-20 * dx, 0.5)
        # grid (create squares around metric values)
        for ii in range(1, len(tmp)):
            ax.axhline(ii, color="k", linestyle="-", linewidth=1)
        for ii in range(1, len(tmp[0])):
            ax.axvline(ii, color="k", linestyle="-", linewidth=1)
        # write metric value in each square (standardized value!)
        if write_metrics is True:
            for jj in range(len(tmp[0])):
                for ii in range(len(tmp)):
                    if tmp.mask[ii, jj] is False:
                        plt.text(
                            jj + 0.5,
                            ii + 0.5,
                            str(round(tmp[ii, jj], 1)),
                            fontsize=10,
                            ha="center",
                            va="center",
                        )
        if kk == len(tab) - 1:
            x2 = ax.get_position().x1
            y1 = ax.get_position().y0
            y2 = ax.get_position().y1
        count += len(tmp[0]) + nbr_space
    # color bar
    cax = plt.axes([x2 + 0.03, y1, 0.02, y2 - y1])
    cbar = plt.colorbar(
        cs,
        cax=cax,
        orientation="vertical",
        ticks=levels,
        pad=0.05,
        extend="both",
        aspect=40,
    )
    cbar.ax.set_yticklabels(
        ["-2 $\sigma$", "-1", "MMV", "1", "2 $\sigma$"], fontdict=fontdict  # noqa
    )
    dict_arrow = dict(facecolor="k", width=8, headwidth=40, headlength=40, shrink=0.0)
    dict_txt = dict(fontsize=40, rotation="vertical", ha="center", weight="bold")
    cax.annotate(
        "",
        xy=(3.7, 0.06),
        xycoords="axes fraction",
        xytext=(3.7, 0.45),
        arrowprops=dict_arrow,
    )
    cax.text(5.2, -0.55, "closer to reference", va="top", **dict_txt)
    cax.annotate(
        "",
        xy=(3.7, 0.94),
        xycoords="axes fraction",
        xytext=(3.7, 0.55),
        arrowprops=dict_arrow,
    )
    cax.text(5.2, 0.55, "further from reference", va="bottom", **dict_txt)
    plt.savefig(name_plot, bbox_inches="tight")
    return fig


def read_data(filename_json):
    """
    Reads given json file (must have usual PMP's structure)

    Input:
    -----
    :param filename_json: string
        Path and name of a json file output of the CLIVAR ENSO metrics package.

    Output:
    ------
    :return data: dictionary
        Dictionary output of the CLIVAR ENSO metrics package, first level is models, second is members.
    """
    with open(filename_json) as ff:
        data = json.load(ff)
    ff.close()
    data = data["RESULTS"]["model"]
    return data


def read_obs(filename_json, obsvation_names, list_met, metric_collection):
    """
    Reads given json file (must have usual PMP's structure) and read given obs

    Input:
    -----
    :param filename_json: string
        Path and name of a json file output of the CLIVAR ENSO metrics package.
    :param obsvation_names: list of string
        Names of wanted additional observations for the portrait plot
    :param list_met: list of string
        List of metrics.
    :param metric_collection: string
        Name of a metric collection.

    Output:
    ------
    :return data: list
        Dictionary output of additional observations metric values.
    """
    data_json = read_data(filename_json)
    dict_out = dict()
    for obs in obsvation_names:
        for met in list_met:
            ref = get_reference(metric_collection, met)
            if obs == "20CRv2":
                if "Ssh" not in met:
                    try:
                        tab = data_json["20CRv2"]["r1i1p1"]["value"][met]["metric"]
                    except KeyError:
                        tab = data_json["20CRv2_20CRv2"]["r1i1p1"]["value"][met][
                            "metric"
                        ]
            elif obs == "NCEP2":
                if "TauxSsh" in met or "SshSst" in met:
                    tab = data_json["NCEP2_GODAS"]["r1i1p1"]["value"][met]["metric"]
                elif "Ssh" in met:
                    tab = data_json["GODAS"]["r1i1p1"]["value"][met]["metric"]
                else:
                    try:
                        tab = data_json["NCEP2"]["r1i1p1"]["value"][met]["metric"]
                    except KeyError:
                        tab = data_json["NCEP2_NCEP2"]["r1i1p1"]["value"][met]["metric"]
            elif obs == "ERA-Interim":
                if "SstMap" in met:
                    tab = {ref: {"value": 0}}
                elif "TauxSsh" in met or "SshSst" in met:
                    tab = data_json["ERA-Interim_SODA3.4.2"]["r1i1p1"]["value"][met][
                        "metric"
                    ]
                elif "Ssh" in met:
                    tab = data_json["SODA3.4.2"]["r1i1p1"]["value"][met]["metric"]
                else:
                    try:
                        tab = data_json["ERA-Interim"]["r1i1p1"]["value"][met]["metric"]
                    except KeyError:
                        tab = data_json["ERA-Interim_ERA-Interim"]["r1i1p1"]["value"][
                            met
                        ]["metric"]

            try:
                val = tab[ref]["value"]
            except KeyError:
                val = 1e20

            try:
                dict_out[obs]
            except KeyError:
                dict_out[obs] = {met: val}
            else:
                dict_out[obs][met] = val

            del ref, val
    return dict_out


def remove_metrics(list_met, metric_collection):
    """
    Removes some metrics from given list

    Inputs:
    ------
    :param list_met: list of string
        List of metrics.
    :param metric_collection: string
        Name of a metric collection.

    Output:
    ------
    :return list_met_out: list of string
        Input list of metrics minus some metrics depending on given metric collection.
    """
    if metric_collection == "ENSO_perf":
        to_remove = [
            "BiasSshLatRmse",
            "BiasSshLonRmse",
            "BiasSstLatRmse",
            "BiasTauxLatRmse",
            "EnsoPrTsRmse",
            "EnsoSstDiversity_1",
            "EnsoTauxTsRmse",
            "NinaSstDur_1",
            "NinaSstDur_2",
            "NinaSstLonRmse_1",
            "NinaSstLonRmse_2",
            "NinaSstTsRmse_1",
            "NinaSstTsRmse_2",
            "NinoSstDiversity_1",
            "NinoSstDiversity_2",
            "NinoSstDur_1",
            "NinoSstDur_2",
            "NinoSstLonRmse_1",
            "NinoSstLonRmse_2",
            "NinoSstTsRmse_1",
            "NinoSstTsRmse_2",
            "SeasonalSshLatRmse",
            "SeasonalSshLonRmse",
            "SeasonalSstLatRmse",
            "SeasonalTauxLatRmse",
        ]
    elif metric_collection == "ENSO_proc":
        to_remove = [
            "BiasSshLonRmse",
            "EnsodSstOce_1",
            "EnsoFbSstLhf",
            "EnsoFbSstLwr",
            "EnsoFbSstShf",
            "EnsoFbSstSwr",
        ]
    else:
        to_remove = [
            "EnsoPrMapCorr",
            "EnsoPrMapRmse",
            "EnsoPrMapStd",
            "EnsoPrMapDjfCorr",
            "EnsoPrMapDjfStd",
            "EnsoPrMapJjaCorr",
            "EnsoPrMapJjaStd",
            "EnsoSlpMapCorr",
            "EnsoSlpMapRmse",
            "EnsoSlpMapStd",
            "EnsoSlpMapDjfCorr",
            "EnsoSlpMapDjfRmse",
            "EnsoSlpMapDjfStd",
            "EnsoSlpMapJjaCorr",
            "EnsoSlpMapJjaRmse",
            "EnsoSlpMapJjaStd",
            "EnsoSstMapCorr",
            "EnsoSstMapRmse",
            "EnsoSstMapStd",
            "EnsoSstMapDjfCorr",
            "EnsoSstMapDjfStd",
            "EnsoSstMapJjaCorr",
            "EnsoSstMapJjaStd",
        ]
    # remove given metrics
    list_met_out = sorted(list(set(list_met) - set(to_remove)), key=lambda v: v.upper())
    return list_met_out
