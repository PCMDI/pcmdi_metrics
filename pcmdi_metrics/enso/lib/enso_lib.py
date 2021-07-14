from __future__ import print_function
from collections import defaultdict
from pcmdi_metrics.driver.pmp_parser import PMPParser

import collections
import copy
import datetime
import glob
import os
import pcmdi_metrics
import re


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


def find_realm(varname, mip):
    if varname in ["tos", "tauuo", "zos", "areacello", "SSH", "ssh"]:
        if mip == "CLIVAR_LE":
            realm = "Omon"
        else:
            realm = "ocean"
        areacell_in_file = "areacello"
    else:
        if mip == "CLIVAR_LE":
            realm = "Amon"
        else:
            realm = "atmos"
        areacell_in_file = "areacella"
    return realm, areacell_in_file


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

    if not os.path.isfile(path_to_return):
        path_to_return = None

    return path_to_return


def CLIVAR_LargeEnsemble_Variables():
    dict_cmip_variables = {
        'reference': 'http://cfconventions.org/Data/cf-standard-names/46/build/cf-standard-name-table.html',
        'variable_name_in_file': {
            # line keys:
            # '<internal_metrics_variable_name>':{'var_name':'<var_name_in_file>','cf_name':<as per ref above>,
            #                                     'cf_unit':'<unit_in_file>'}
            # areacell
            'areacell': {'var_name': 'areacella', 'cf_name': 'cell_area', 'cf_units': 'm2'},
            # landmask
            'landmask': {'var_name': 'sftlf', 'cf_name': 'cell_area', 'cf_units': '1'},
            # latent heat flux (on ocean grid or ocean points only)
            'lhf': {'var_name': 'hfls', 'cf_name': 'surface_upward_latent_heat_flux', 'cf_units': 'W m-2'},
            # longwave radiation computed from these variables IN THAT ORDER (on ocean grid or ocean points only)
            # lwr = rlds - rlus
            # sometimes lwr is included in the datasets in a variable called 'rls'
            'lwr': {'var_name': 'flns', 'cf_name': 'net_longwave_flux_at_surface', 'cf_units': 'W m-2'},
            # Rainfall Flux
            'pr': {'var_name': 'pr', 'cf_name': 'precipitation_flux', 'cf_units': 'kg m-2 s-1'},
            # Sea Level Pressure
            'slp': {'var_name': 'psl', 'cf_name': 'air_pressure_at_sea_level', 'cf_units': 'Pa'},
            # sensible heat flux (on ocean grid or ocean points only)
            'shf': {'var_name': 'hfss', 'cf_name': 'surface_upward_sensible_heat_flux', 'cf_units': 'W m-2'},
            # sea surface height
            'ssh': {'var_name': 'ssh', 'cf_name': 'Sea Surface Height', 'cf_units': 'm'},
            # sea surface temperature
            'sst': {'var_name': 'ts', 'cf_name': 'surface_temperature', 'cf_units': 'K'},
            # shortwave radiation computed from these variables IN THAT ORDER
            # swr = rsds - rsus
            # sometimes swr is included in the datasets in a variable called 'rss'
            'swr': {'var_name': 'fsns', 'cf_name': 'net_shortwave_flux_at_surface', 'cf_units': 'W m-2'},
            # zonal surface wind stress
            'taux': {'var_name': 'tauu', 'cf_name': 'surface_downward_eastward_stress', 'cf_units': 'Pa'},
            # total heat flux computed from these variables IN THAT ORDER
            # tfh = hfls + hfss + rlds - rlus + rsds - rsus
            # sometimes rls = rlds - rlus and rss = rsds - rsus
            # sometimes thf is included in the datasets in a variable called 'hfds', 'netflux', 'thflx',...
            'thf': {
                'var_name': ['hfls', 'hfss', 'flns', 'fsns'],
                'cf_name': ['surface_upward_latent_heat_flux', 'surface_upward_sensible_heat_flux',
                            'net_longwave_flux_at_surface',
                            'net_shortwave_flux_at_surface'],
                'cf_units': 'W m-2', 'algebric_calculation': ['plus', 'plus', 'plus', 'plus']
            },
        },
    }
    return dict_cmip_variables


def sort_human(input_list):
    lst = copy.copy(input_list)

    def convert(text):
        return int(text) if text.isdigit() else text

    def alphanum(key):
        return [convert(c) for c in re.split('([0-9]+)', key)]

    lst.sort(key=alphanum)
    return lst


def match_obs_name(obs):
    # Match dataset name between obs catalogue and ENSO code
    dict_obs_name = {
        '20CR': '20CRv2',
        'AVISO-1-0': 'AVISO',
        'CMAP-V1902': 'CMAP',
        'ERA-INT': 'ERA-Interim',
        'GPCP-2-3': 'GPCPv2.3',
        'HadISST-1-1': 'HadISST',
        'TropFlux-1-0': 'Tropflux'
    }
    """
    in ENSO package: ['20CRv2', '20CRv3', 'AVISO', 'CFSR', 'CMAP', 'ERA-Interim', 'ERSSTv5',
                      'GODAS', 'GPCPv2.3', 'HadISST', 'NCEP2',
                      'OAFlux', 'OISST', 'ORAS4', 'SODA3.4.2', 'Tropflux']
    in PMPobs catalogue: ['20CR', 'AVISO-1-0', 'CERES-EBAF-4-0', 'CERES-EBAF-4-1', 'CMAP-V1902',
                          'ERA-20C', 'ERA-40', 'ERA-5', 'ERA-INT', 'GPCP-2-3', 'HadISST-1-1',
                          'ISCCP', 'REMSS-PRW-v07r01', 'TRMM-3B43v-7', 'TropFlux-1-0']
    """

    if obs in list(dict_obs_name.keys()):
        obs_name = dict_obs_name[obs]
    else:
        obs_name = obs

    return obs_name
