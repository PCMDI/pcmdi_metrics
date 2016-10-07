import argparse
import os
from pcmdi_metrics.PMP.PMPDriver import *
from pcmdi_metrics.PMP.PMPParameter import *

parser = argparse.ArgumentParser(
    description='Runs PCMDI Metrics Diagnostics')

parser.add_argument(
    "-p", "--parameters",
    dest="user_parameter_file_path",
    default="",
    help="Path to the user-defined parameter file",
    required=False)


args = parser.parse_args()
parameter = PMPParameter()
if args.user_parameter_file_path is not '':
    parameter.import_user_parameter_file_as_module(
        args.user_parameter_file_path
    )

else:
    parameter.dry_run = False
    parameter.case_id = 'installationTest'
    parameter.test_data_set = ['GFDL-ESM2G']
    parameter.simulation_description_mapping = {
        "Login": "Login",
        "Center": "Center",
        "SimTrackingDate": "creation_date"}
    parameter.vars = ['tos', 'tas']

    parameter.model_tweaks = {
        # Keys are model acronym or None which applies to all model entries
        None: {
            # Variables name mapping
            "variable_mapping": {"tos": "tos"},
        },
        "GFDL-ESM2G": {
            "variable_mapping": {"tas": "tas_ac"},
        },
    }
    parameter.regions = {"tas": [None, "terre", "ocean"], "tos": [None, ]}
    parameter.regions_values = {"terre": 100.}

    parameter.reference_data_set = ['all']
    parameter.ext = '.nc'

    parameter.target_grid = '2.5x2.5'  # '2.5x2.5' or actual cdms2 grid object
    parameter.regrid_tool = 'regrid2'  # OPTIONS: 'regrid2','esmf'
    parameter.regrid_method = 'linear'
    parameter.regrid_tool_ocn = 'esmf'  # OPTIONS: "regrid2","esmf"
    parameter.regrid_method_ocn = 'linear'

    parameter.period = '198501-200512'
    parameter.realization = 'r1i1p1'
    parameter.save_mod_clims = True  # True or False

    parameter.filename_template = \
        "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(period)-clim.nc"
    parameter.sftlf_filename_template = "sftlf_%(model_version).nc"

    pth = os.path.dirname(__file__)
    parameter.mod_data_path = os.path.abspath(os.path.join(pth, "data"))
    parameter.obs_data_path = os.path.abspath(os.path.join(pth, "obs"))

    parameter.custom_observations = os.path.abspath(
        os.path.join(
            parameter.obs_data_path,
            "obs_info_dictionary.json"))
    # DIRECTORY WHERE TO PUT RESULTS
    parameter.metrics_output_path = os.path.join(
        'pcmdi_install_test_results',
        'metrics_results', "%(case_id)")
    # DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
    parameter.model_clims_interpolated_output = os.path.join(
        'pcmdi_install_test_results',
        'interpolated_model_clims')
    # FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
    parameter.filename_output_template = "%(variable)%(level)_" + \
        "%(model_version)_%(table)_historical_%(realization)_%(period)" + \
        ".interpolated.%(regrid_method).%(target_grid_name)-clim%(ext)"

driver = PMPDriver(parameter)
driver.run()
