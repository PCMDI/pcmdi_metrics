from __future__ import print_function
from collections import defaultdict
from pcmdi_metrics.driver.pmp_parser import PMPParser

import collections
import datetime
import glob
import os
import pcmdi_metrics


def AddParserArgument():

    P = PMPParser()  # Includes all default options

    P.add_argument("--mip",
                   type=str,
                   default="cmip5",
                   help="A WCRP MIP project such as CMIP3 and CMIP5")
    P.add_argument("--exp",
                   type=str,
                   default="historical",
                   help="An experiment such as AMIP, historical or pi-contorl")
    P.use("--modpath")
    P.add_argument("--modpath_lf",
                   type=str,
                   dest='modpath_lf',
                   help="Directory path to model land fraction field")
    P.add_argument("--modnames",
                   type=str,
                   nargs='+',
                   default=None,
                   help="List of models")
    P.add_argument("-r", "--realization",
                   type=str,
                   default="r1i1p1",
                   help="Consider all accessible realizations as idividual\n"
                        "- r1i1p1: default, consider only 'r1i1p1' member\n"
                        "          Or, specify realization, e.g, r3i1p1'\n"
                        "- *: consider all available realizations")
    P.use("--reference_data_path")
    P.add_argument("--reference_data_lf_path",
                   type=str,
                   dest='reference_data_lf_path',
                   help="Data path to land fraction of reference dataset")
    P.add_argument("--metricsCollection",
                   type=str,
                   dest='metricsCollection',
                   default="ENSO_perf",
                   help="Metrics Collection e.g. ENSO_perf, ENSO_tel, or ENSO_proc")
    P.add_argument("--json_name",
                   type=str,
                   dest='json_name',
                   help="File name for output JSON")
    P.add_argument("--netcdf_name",
                   type=str,
                   dest='netcdf_name',
                   help="File name for output NetCDF")
    P.use("--results_dir")
    P.add_argument("--case_id",
                   type=str,
                   dest="case_id",
                   default="{:v%Y%m%d}".format(datetime.datetime.now()),
                   help="version as date, e.g., v20191116 (yyyy-mm-dd)")
    P.add_argument("--obs_catalogue",
                   type=str,
                   default=None,
                   dest='obs_catalogue',
                   help="obs_catalogue JSON file for CMORized observation, default is None")
    P.add_argument("--obs_cmor_path",
                   type=str,
                   default=None,
                   dest='obs_cmor_path',
                   help="Directory path for CMORized observation dataset, default is None")
    # Switches
    P.add_argument("-d", "--debug", nargs='?',
                   const=True, default=False,
                   type=bool,
                   help="Option for debug: True / False (defualt)")
    P.add_argument("--obs_cmor", nargs='?',
                   const=True, default=False,
                   type=bool,
                   help="Use CMORized reference database?: True / False (defualt)")
    P.add_argument("--nc_out", nargs='?',
                   const=True, default=True,
                   type=bool,
                   help="Option for generate netCDF file output: True (default) / False")

    param = P.get_parameter()

    return param


# Dictionary to save result
def tree(): return defaultdict(tree)


# Prepare outputing metrics to JSON file
def metrics_to_json(mc_name, dict_obs, dict_metric, dict_dive, egg_pth, outdir, json_name, mod=None, run=None):
    # disclaimer and reference for JSON header
    disclaimer = open(
        os.path.join(
            egg_pth,
            "disclaimer.txt")).read()

    if mc_name == 'MC1':
        reference = ("The statistics in this file are based on Bellenger et al. " +
                     "Clim Dyn (2014) 42:1999-2018. doi:10.1007/s00382-013-1783-z")
    elif mc_name == 'ENSO_perf':
        reference = "MC for ENSO Performance..."
    elif mc_name == 'ENSO_tel':
        reference = "MC for ENSO Teleconnection..."
    elif mc_name == 'ENSO_proc':
        reference = "MC for ENSO Process..."
    else:
        reference = mc_name

    enso_stat_dic = tree()  # Use tree dictionary to avoid declearing everytime

    # First JSON for metrics results
    enso_stat_dic['obs'] = dict_obs
    if mod is not None and run is not None:
        enso_stat_dic['model'][mod][run] = dict_metric[mod][run]
    else:
        enso_stat_dic['model'] = dict_metric
    metrics_dictionary = collections.OrderedDict()
    metrics_dictionary["DISCLAIMER"] = disclaimer
    metrics_dictionary["REFERENCE"] = reference
    metrics_dictionary["RESULTS"] = enso_stat_dic

    OUT = pcmdi_metrics.io.base.Base(outdir(output_type='metrics_results'), json_name+'.json')
    OUT.write(
        metrics_dictionary,
        json_structure=["type", "data", "metric", "item", "value or description"],
        indent=4,
        separators=(
            ',',
            ': '),
        sort_keys=True)

    # Second JSON for dive down information
    diveDown_dictionary = collections.OrderedDict()
    diveDown_dictionary["DISCLAIMER"] = disclaimer
    diveDown_dictionary["REFERENCE"] = reference
    diveDown_dictionary["RESULTS"] = {}
    if mod is not None and run is not None:
        diveDown_dictionary["RESULTS"]["model"] = {}
        diveDown_dictionary["RESULTS"]["model"][mod] = {}
        diveDown_dictionary["RESULTS"]["model"][mod][run] = {}
        diveDown_dictionary["RESULTS"]["model"][mod][run] = dict_dive[mod][run]
    else:
        diveDown_dictionary["RESULTS"]["model"] = dict_dive

    OUT2 = pcmdi_metrics.io.base.Base(outdir(output_type='metrics_results'), json_name+'_diveDown.json')
    OUT2.write(
        dict_dive,
        json_structure=["type", "data", "metric", "item", "value or description"],
        indent=4,
        separators=(
            ',',
            ': '),
        sort_keys=True)


def find_realm(varname):
    if varname in ["tos", "tauuo", "zos", "areacello", "SSH", "ssh"]:
        realm = "ocean"
        # realm = "Omon"
        areacell_in_file = "areacello"
    else:
        realm = "atmos"
        # realm = "Amon"
        areacell_in_file = "areacella"
    return areacell_in_file, realm


def get_file(path):
    file_list = glob.glob(path)
    print("path: ", path)
    print("file_list: ", file_list)
    if len(file_list) > 1:
        print("Multiple files detected in get_file function. file_list: ", file_list)
        path_to_return = sorted(file_list)[0]
    elif len(file_list) == 1:
        path_to_return = file_list[0]
    elif len(file_list) == 0:
        path_to_return = path
    return path_to_return


def getListOfFiles(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles    