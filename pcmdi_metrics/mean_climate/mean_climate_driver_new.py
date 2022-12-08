#!/usr/bin/env python

import json
import os
from re import split

import cdms2
import cdutil
import xcdat

from pcmdi_metrics import resources
from pcmdi_metrics.io import xcdat_open
from pcmdi_metrics.io import load_regions_specs, region_subset
from pcmdi_metrics.mean_climate.lib import create_mean_climate_parser
from pcmdi_metrics.mean_climate.lib import compute_metrics
from pcmdi_metrics.variability_mode.lib import tree


def main():
    parser = create_mean_climate_parser()
    parameter = parser.get_parameter(cmd_default_vars=False, argparse_vals_only=False)

    # parameters
    case_id = parameter.case_id
    test_data_set = parameter.test_data_set
    vars = parameter.vars
    reference_data_set = parameter.reference_data_set
    target_grid = parameter.target_grid
    regrid_tool = parameter.regrid_tool
    regrid_method = parameter.regrid_method
    regrid_tool_ocn = parameter.regrid_tool_ocn
    save_test_clims = parameter.save_test_clims
    test_clims_interpolated_output = parameter.test_clims_interpolated_output
    filename_template = parameter.filename_template
    sftlf_filename_template = parameter.sftlf_filename_template
    generate_sftlf = parameter.generate_sftlf
    regions = parameter.regions
    test_data_path = parameter.test_data_path
    reference_data_path = parameter.reference_data_path
    metrics_output_path = parameter.metrics_output_path

    debug = True

    print(
        'case_id: ', case_id, '\n',
        'test_data_set:', test_data_set, '\n',
        'vars:', vars, '\n',
        'reference_data_set:', reference_data_set, '\n',
        'target_grid:', target_grid, '\n',
        'regrid_tool:', regrid_tool, '\n',
        'regrid_method:', regrid_method, '\n',
        'regrid_tool_ocn:', regrid_tool_ocn, '\n',
        'save_test_clims:', save_test_clims, '\n',
        'test_clims_interpolated_output:', test_clims_interpolated_output, '\n',
        'filename_template:', filename_template, '\n',
        'sftlf_filename_template:', sftlf_filename_template, '\n',
        'generate_sftlf:', generate_sftlf, '\n',
        'regions:', regions, '\n',
        'test_data_path:', test_data_path, '\n',
        'reference_data_path:', reference_data_path, '\n',
        'metrics_output_path:', metrics_output_path, '\n')

    print('--- prepare mean climate metrics calculation ---')

    regions_specs = load_regions_specs()
    default_regions = ['global', 'NHEX', 'SHEX', 'TROPICS']

    # generate target grid
    if target_grid == "2.5x2.5":
        t_grid = xcdat.create_uniform_grid(-88.875, 88.625, 2.5, 0, 357.5, 2.5)
        print('type(t_grid):', type(t_grid))
        t_grid_cdms2 = cdms2.createUniformGrid(-88.875, 72, 2.5, 0, 144, 2.5)
        sft = cdutil.generateLandSeaMask(t_grid_cdms2)

    # load obs catalogue json
    egg_pth = resources.resource_path()
    obs_file_name = "obs_info_dictionary.json"
    obs_file_path = os.path.join(egg_pth, obs_file_name)
    with open(obs_file_path) as fo:
        obs_dict = json.loads(fo.read())
    if debug:
        print('obs_dict:', json.dumps(obs_dict, indent=4, sort_keys=True))

    # set dictionary for .json record
    result_dict = tree()

    print('--- start mean climate metrics calculation ---')

    # -------------
    # variable loop
    # -------------
    for var in vars:

        if '_' in var or '-' in var:
            varname = split('_|-', var)[0]
            level = float(split('_|-', var)[1])
        else:
            varname = var
            level = None

        if varname not in list(regions.keys()):
            regions[varname] = default_regions

        print('varname:', varname)
        print('level:', level)

        # ----------------
        # observation loop
        # ----------------
        for ref in reference_data_set:
            print('ref:', ref)
            # identify data to load (annual cycle (AC) data is loading in)
            ref_dataset_name = obs_dict[varname][ref]
            ref_data_full_path = os.path.join(
                reference_data_path,
                obs_dict[varname][ref_dataset_name]["template"])
            print('ref_data_full_path:', ref_data_full_path)
            # load data and regrid
            ds_ref = load_and_regrid(ref_data_full_path, varname, level, t_grid, decode_times=False, regrid_tool=regrid_tool, debug=debug)
            ds_ref_dict = dict()

            # ----------
            # model loop
            # ----------
            for model in test_data_set:
                print('model:', model)
                ds_model_dict = dict()
                # identify data to load (annual cycle (AC) data is loading in)
                model_data_full_path = os.path.join(
                    test_data_path,
                    filename_template.replace('%(variable)', varname).replace('%(model)', model))
                # load data and regrid
                ds_model = load_and_regrid(model_data_full_path, varname, level, t_grid, regrid_tool=regrid_tool, debug=debug)

                # -----------
                # region loop
                # -----------
                for region in regions[varname]:
                    print('region:', region)

                    # land/sea mask
                    if region.split('_')[0] in ['land', 'ocean']:
                        is_masking = True
                    else:
                        is_masking = False

                    # spatial subset
                    if region.lower() in ['global', 'land', 'ocean']:
                        ds_model_dict[region] = ds_model
                        if region not in list(ds_ref_dict.keys()):
                            ds_ref_dict[region] = ds_ref
                    else:
                        ds_model_dict[region] = region_subset(ds_model, region_specs, region=region)
                        if region not in list(ds_ref_dict.keys()):
                            ds_ref_dict[region] = region_subset(ds_ref, region_specs, region=region)

                    # compute metrics
                    result_dict["RESULTS"][model][ref][region] = compute_metrics(varname, ds_model_dict[region], ds_ref_dict[region])

                # write JSON for single model / single obs (need to accumulate later) / single variable
                print('result_dict:', result_dict)

        # write JSON for all models / all obs / single variable
        if debug:
            print('result_dict:', json.dumps(result_dict, indent=4, sort_keys=True))


def load_and_regrid(data_path, varname, level=None, t_grid=None, decode_times=True, regrid_tool='regrid2', debug=False):
    """Load data and regrid to target grid

    Args:
        data_path (str): full data path for nc or xml file
        varname (str): variable name
        level (float): level to extract (unit in hPa)
        t_grid (xarray.core.dataset.Dataset): target grid to regrid
        decode_times (bool): Default is True. decode_times=False will be removed once obs4MIP written using xcdat
        regrid_tool (str): Name of the regridding tool. See https://xcdat.readthedocs.io/en/stable/generated/xarray.Dataset.regridder.horizontal.html for more info
        debug (bool): Default is False. If True, print more info to help debugging process
    """
    # load data
    ds = xcdat_open(data_path, data_var=varname, decode_times=decode_times)  # NOTE: decode_times=False will be removed once obs4MIP written using xcdat
    if level is not None:
        level = level * 100  # hPa to Pa
        ds = ds.sel(plev=level)
    if debug:
        print('ds:', ds)
    # regrid
    ds_regridded = ds.regridder.horizontal(varname, t_grid, tool=regrid_tool)
    if debug:
        print('ds_regridded:', ds_regridded)
    return ds_regridded



if __name__ == "__main__":
    main()
