#!/usr/bin/env python

import argparse
import getopt
import json
import os
import pdb  # , pdb.set_trace()
import string
import sys
import pcmdi_metrics
import matplotlib.pyplot as PLT
import numpy as NP

# from pcmdi_metrics.mean_climate_plots import BarChart
from argparse import RawTextHelpFormatter
from SeabarChart_mpl import BarChart
from pcmdi_metrics.driver import pmp_parser

test = False
# test = True

P = pmp_parser.PMPParser(description="Runs PCMDI Monsoon Computations")

P.add_argument("-j", "--json", type=str, dest="json", help="Path to json file")
P.add_argument(
    "--aj",
    "--aux_json_path",
    type=str,
    dest="aux_json_path",
    default="",
    help="Path to auxillary json file",
)
P.add_argument(
    "-v", "--variable", type=str, dest="variable", default="", help="(Case Insensitive)"
)
P.add_argument(
    "-s",
    "--stat",
    type=str,
    default="rms",
    help="Statistic:\n" "- Available options: bias, cor, rms",
)
P.add_argument(
    "--seas",
    "--season",
    type=str,
    dest="season",
    default="all",
    help="Season\n" "- Available options: DJF (default), MAM, JJA, SON or all",
)
P.add_argument(
    "-r",
    "--reference",
    type=str,
    dest="reference",
    default="defaultReference",
    help="Reference against which the statistics are computed\n"
    "- Available options: defaultReference (default), alternate1, alternate2",
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
    "-d", "--domain", type=str, dest="domain", default="global", help="put options here"
)
P.add_argument("-p", "--parameters", type=str, dest="parameters", default="", help="")
P.add_argument(
    "-t",
    "--title",
    type=str,
    dest="title",
    default="",
    help="Main title (top of the page)",
)
P.add_argument(
    "--yax",
    "--yaxis_label",
    type=str,
    dest="yaxis_label",
    default="",
    help="Label of the Y axis",
)
P.add_argument("-o", "--outpath", type=str, dest="outpath", default=".", help="")
P.add_argument(
    "--hi",
    "--highlights",
    type=str,
    dest="highlights",
    default="",
    help="Names of the simulations (as they appear on the plot) that will be highlighted\n"
    "with a different color than the default color (blue).\n"
    "The user can provide a list of colors with -cl; otherwise, they will appear in green.",
)
P.add_argument(
    "--cn",
    "--customname",
    type=str,
    dest="customname",
    default="",
    help="Custom name for the name of the simulation(s) in the plot\n"
    "- the user can pass one customname by auxillary json file \n"
    "  separated by commas (,) and no space => Ex: Sim1,Sim2",
)
P.add_argument(
    "--kp",
    "--keywords",
    type=str,
    dest="keywords",
    default="",
    help="Keywords to build the name of the simulation in the plot\n"
    "- Available options: SimulationModel, Model_period, Realization\n"
    "- the user can pass two keywords separated by commas (), \n"
    "  and no space => Realization,Model_period",
)
P.add_argument(
    "--cl",
    "--colors",
    type=str,
    dest="colors",
    default="g",
    help="Colors for the simulations in the auxillary json files\n"
    "The user can pass either one color for all auxillary simulations or\n"
    "or one color per json file (separated by commas=> Ex: g,b,r)",
)


args = P.get_parameters()

json_path = args.json
aux_json_path = args.aux_json_path
variable = args.variable
domain = args.domain
experiment = args.experiment
stat = args.stat
outpath = args.outpath
customname = args.customname
reference = args.reference
season = args.season
colors = args.colors
keywords = args.keywords
title = args.title
yaxis_label = args.yaxis_label
highlights = args.highlights

print("-----------------------------")
print("--")
print("-- Working on:")
print("-> json_path (-j) : " + json_path)
print("-> aux_json_path (-aj) : " + aux_json_path)
print("-> stat (-s) : " + stat)
print("-> outpath (-o): " + outpath)
print("-> experiment (-e) : " + experiment)
print("-> variable (-v) : " + variable)
print("-> domain (-d) : " + domain)
print("-> reference (-r) : " + reference)
print("-> customname (-cn) : " + customname)
print("-> season (-seas) " + season)
print("-> colors (-cl) " + colors)
print("-> keywords (-kp) " + keywords)
print("-> parameters (-p) " + args.parameters)
print("-> yaxis_label (-yax) " + yaxis_label)
print("-> highlights (-hi) " + highlights)
print("-----------------------------")

print("==> Loading json file : " + json_path)
print("...")
from pcmdi_metrics.pcmdi.io import JSONs

try:
    fj = open(json_path)
    fj.close()
except:
    json_path = json_path.replace("@VAR", variable)

print("==> json file loaded")

# --> aux_json_path can be a path, a json_file;
# --> It could also be possible to pass a list of json files:
# -->   - via a list
# -->   - or a dictionary with a CustomName


# -- Exploring a way to handle an auxillary json file
try:
    aux_mods = ""
    custom_names = {}
    aux_jsons = []
    if aux_json_path:
        print("==> Loading auxillary json file : " + aux_json_path)
        print("...")
        # -- Case: aux_json_path contains multiple paths separated by commas (,)
        aux_jsons = str.split(aux_json_path, ",")
        aux_dd = dict(RESULTS=dict())
        inc = 1
        # -- Replace @VAR by var (if var was passed by the user)
        if variable:
            for i in xrange(len(aux_jsons)):
                aux_jsons[i] = aux_jsons[i].replace("@VAR", variable)
        # -- Loop on the files to reconstruct new mod names
        for aux_json in aux_jsons:
            #
            # -- add the results to aux_mods:
            # --   - 1. if we have a custom name, use it as the new name (new_mod_name)
            # --   - 2. use keywords if we have keywords to construct the new name
            # --   - 3. add an increment to the model name if this name is already in aux_dd
            # --   -->  if not in 1, 2 or 3, leave the dictionary as it is
            new_mod_name = ""
            if customname:
                # - 1. if we have a custom name, use it as the new name (new_mod_name)
                customnames = customname.split(",")
                new_mod_name = customnames[aux_jsons.index(aux_json)]
            # elif keywords:
            #    # - 2. use keywords if we have keywords to construct the new name
            #    customname_kw = keywords.split(',')
            #    for kw in customname_kw:
            #        if not new_mod_name:
            #           new_mod_name = tmp_dict['RESULTS'][mod_name]['SimulationDescription'][kw]
            #        else:
            # new_mod_name = new_mod_name+'
            # '+tmp_dict['RESULTS'][mod_name]['SimulationDescription'][kw]
            elif mod_name in aux_dd:
                # - 3. add an increment to the model name if this name is already in aux_dd
                new_mod_name = mod_name + "_" + inc
                inc = inc + 1
            if new_mod_name:
                custom_names[mod_name] = new_mod_name
                #
        print("==> Auxillary json file loaded")
    elif numexpts:
        # -- If the user gave a list of simulations via 'numexpts' in the parameter file:
        for numexp in numexpts:
            # -- First, we see if it is a dictionary (with customnames) or a list
            if isinstance(numexpts, dict):
                numexp_json = numexpts[numexp]
            else:
                numexp_json = numexp
            # -- Then, we try to open the json file
            try:
                numexp_fj = open(numexp_json)
                numexp_fj.close()
            except:
                numexp_json = numexp_json.replace("@VAR", variable)
            numexp_fj = open(numexp_json)
            aux_jsons.append(numexp_json)
            #
            new_mod_name = False
            if isinstance(numexpts, dict):
                tmp = json.load(numexp_fj)
                mod_name = tmp["RESULTS"].keys()[0]
                custom_names[mod_name] = numexp
            #
            # -- Add the results to the auxillary dictionary
            numexp_fj.close()

except Exception as err:
    print("ERROR READING IN Aux:", err)
    pass

J = JSONs(
    [
        json_path,
    ]
)
dd = J()
mods = dd.getAxis(dd.getAxisIndex("model"))
mods = sorted(mods, key=lambda s: s.lower())
# !!!!!!!!
tot_mods = mods
if len(aux_jsons) > 0:
    Jaux = JSONS(aux_jsons)
    dd_aux = Jaux()
    aux_mods = dd_aux.getAxisIndex(dd_aux.getAxisIndex("model"))
    tot_mods += aux_mods
    d2 = MV2.concatenate((dd, dd_aux))
# !!!!!!!!

unit_adj = 1
if variable == "pr":
    unit_adj = 28.0
if variable == "tauu":
    unit_adj = 1000.0


if season == "all":
    seasons = ["ann", "djf", "mam", "jja", "son"]
    rects = {
        "ann": 511,
        "djf": 512,
        "mam": 513,
        "jja": 514,
        "son": 515,
    }  # subplot location
    fig = PLT.figure(figsize=(10, 16))  # optimized figure size for five subplots
    fig_filename = variable + "_" + experiment + "_bias_5panel_" + season + "_" + domain
else:
    rects = {}
    rects[season] = 111  # subplot location
    fig = PLT.figure(figsize=(10, 6))  # optimized figure size for one subplot
    fig_filename = variable + "_" + experiment + "_bias_1panel_" + stat + "_" + domain

# -- Main title of the plot
if not title:
    title = (
        (domain).upper()
        + " "
        + variable.upper()
        + " "
        + stat.upper()
        + " ("
        + experiment.upper()
        + " CMIP5 R1)"
    )
fig.suptitle(title, size="x-large")  # Giving title for the entire canvas


# -- Plot custom parameters
plot_params = dict()
if aux_json_path:
    plot_params.update(highlights=aux_mods)
if highlights:
    plot_params.update(highlights=str.split(highlights, ","))
if colors:
    plot_params.update(colors=colors)
if yaxis_label:
    plot_params.update(yaxis_label=yaxis_label)

print("==>")
print("==> Starting loop on the seasons")
print("==>")

# PJG changing seasons to monsoon domains
seasons = ["AllM", "SAFM", "SAMM", "NAMM", "AUSM"]  # ,'NAFM','ASM']
rects = {
    "AllM": 511,
    "SAFM": 512,
    "SAMM": 513,
    "NAMM": 514,
    "AUSM": 515,
}  # subplot location


for season in seasons:
    print("-> Working on season : " + season)
    print("...")
    all_mods = []
    #   uni = dd['RESULTS'][mods[0]]['units']  PJG ALWAYS PRECIP FOR MPI
    uni = "mm/day"
    # -- Loop on the main json file results
    for mod in tot_mods:
        print("-> Computing " + stat + " on " + mod)
        #       Realization     = dd['RESULTS'][mod]['SimulationDescription']['Realization']
        #       bias = float(dd['RESULTS'][mod][reference][Realization][domain][stat +'_xy_'+season])*unit_adj
        bias = float(dd["RESULTS"][mod][season]["rmsn"])
        all_mods.append(bias)
    # -- Do the bar chart plot with BarChart (pcmdi_metrics.mean_climate_plots.BarChart)
    print("==> Start the plotting...")
    dia = BarChart(tot_mods, all_mods, uni, fig=fig, rect=rects[season], **plot_params)
    print("==> BELOW plotting start...")
    dia._ax.set_title(season.upper())  # Give title for individual subplot
    if (
        season != seasons[-1]
    ):  # Hide x-axis labels for upper panels if plotting multiple panels
        dia._ax.axes.xaxis.set_ticklabels([])
        dia._ax.set_xlabel("")

if len(seasons) == 1:
    fig.subplots_adjust(bottom=0.3)  # Give more bottom margins to model name show up

PLT.savefig(outpath + "/" + fig_filename + ".png")
print("==> Figure saved as : " + outpath + "/" + fig_filename + ".png")
print("==> End of Bar Chart plot")
if test:
    PLT.ion()
    PLT.show()
