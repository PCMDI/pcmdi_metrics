import glob
import json
import os
from typing import Any

import xsearch as xs

"""
This code uses xsearch (https://github.com/PCMDI/xsearch) to generate a dictionary of models and their members
with paths to netcdf files for specified variables, experiment, frequency, and CMIP table.
The dictionary is saved to a json file.

About xsearch
-------------
- xsearch is a software to query CMIP data. It can be used for CMIP data in NERSC.
- This code is written by Jiwoo Lee (LLNL) in September 2025.

To start in NERSC machine (Perlmutter)
--------------------------------------
Prepare environment
~~~~~~~~~~~~~~~~~~~
You will need to add export PYTHONPATH='/global/cfs/projectdirs/m4581/xsearch/software/xsearch/' as a part of your .bashrc file in home directory.

> vi ~/.bashrc      # add: export PYTHONPATH='/global/cfs/projectdirs/m4581/xsearch/software/xsearch/'
> source ~/.bashrc

Installation
~~~~~~~~~~~~
> cd /global/cfs/projectdirs/m4581/xsearch/software/xsearch/
> conda activate [MY_CONDA_ENV_NAME]
> python setup.py install
"""


def main():
    # User options ------------------------------------------------------------------
    # mip_eras = ["CMIP6", "CMIP5"]
    mip_eras = ["CMIP6"]
    # mip_eras = ["CMIP5"]
    # exps = ["historical", "amip"]
    exps = ["historical"]
    # exps = ["amip"]
    # variables = ["psl", "ts"]
    # variables = ["pr"]
    # variables = ["sic"]  # for CMIP5
    variables = ["siconc"]  # for CMIP6
    freq = "mon"
    #cmipTable = "Amon"
    cmipTable = "SImon"  # for siconc variable in CMIP6
    #cmipTable = "OImon"  # for sic variable in CMIP5
    # freq = "day"
    # cmipTable = "day"
    grid = "gn"

    all_ref_variables = False  # if True, use all variables in the ref_catalogue file, otherwise use only those in 'variables' above

    first_member_only = False
    include_lf = True  # include land fraction variable 'sftlf', 'areacella', and 'areacello'

    ref_catalogue = "/global/cfs/projectdirs/m4581/PMP/pmp_reference/catalogue/PMP_obs4MIPsClims_catalogue_byVar_v20250709.json"

    # xml options: A shell script to generate xml files using cdscan will be created
    generate_xmls = False  # if True, generate xml files for the generated json files
    xmls_dir = "/pscratch/sd/l/lee1043/PMP/pmp_input/xml_files"
    xml_cmds_sh = "generate_xml_cmds.sh"  # save the xml generation commands to a shell script file

    # yml options: new recommended method
    generate_ymls = True  # if True, generate yml files for the generated json files
    ymls_dir = "/pscratch/sd/l/lee1043/PMP/pmp_input/yml_files"
    # -------------------------------------------------------------------------------

    if xml_cmds_sh is not None and os.path.exists(xml_cmds_sh):
        os.remove(xml_cmds_sh)

    if all_ref_variables:
        # Load reference catalogue to get variables
        if os.path.exists(ref_catalogue):
            with open(ref_catalogue, "r") as f:
                ref_cat = json.load(f)
            ref_variables = list(ref_cat.keys())
            print("Reference catalogue loaded:", ref_catalogue)
            print("Variables in the reference catalogue:", ref_variables)
            variables = ref_variables

    for mip_era in mip_eras:
        for exp in exps:
            generate_model_catalogue_xsearch(
                mip_era=mip_era,
                exp=exp,
                variables=variables,
                freq=freq,
                cmipTable=cmipTable,
                grid=grid,
                first_member_only=first_member_only,
                include_lf=include_lf,
                generate_xmls=generate_xmls,
                xmls_dir=xmls_dir,
                xml_cmds_sh=xml_cmds_sh,
                generate_ymls=generate_ymls,
                ymls_dir=ymls_dir,
            )


def generate_model_catalogue_xsearch(
    mip_era: str,
    exp: str,
    variables: list[str],
    freq: str,
    cmipTable: str = None,
    grid: str = None,
    first_member_only: bool = False,
    include_lf: bool = True,
    generate_xmls: bool = False,
    xmls_dir: str = None,
    xml_cmds_sh: str = None,
    generate_ymls: bool = False,
    ymls_dir: str = None,
):
    """
    Generate a dictionary of models and their members with paths to netcdf files using xsearch.
    Save the dictionary to a json file.
    """

    models_dict = generate_model_path_dict(
        exp=exp,
        variables=variables,
        freq=freq,
        cmipTable=cmipTable,
        grid=grid,
        mip_era=mip_era,
        first_member_only=first_member_only,
        generate_xmls=generate_xmls,
        xmls_dir=xmls_dir,
        xml_cmds_sh=xml_cmds_sh,
        generate_ymls=generate_ymls,
        ymls_dir=ymls_dir,
    )
    models_dict_combined = models_dict

    if include_lf:
        models_lf_dict_a = generate_model_path_dict(
            exp=exp,
            variables=["sftlf", "areacella"],
            freq="fx",
            cmipTable="fx",
            grid=grid,
            mip_era=mip_era,
            first_member_only=first_member_only,
            generate_xmls=generate_xmls,
            xmls_dir=xmls_dir,
            xml_cmds_sh=xml_cmds_sh,
            generate_ymls=generate_ymls,
            ymls_dir=ymls_dir,
        )

        if mip_era == "CMIP5":
            cmipTable_o = "fx"
        elif mip_era == "CMIP6":
            cmipTable_o = "Ofx"

        models_lf_dict_o = generate_model_path_dict(
            exp=exp,    
            variables=["areacello"],
            freq="fx",      
            cmipTable=cmipTable_o,
            mip_era=mip_era,
            grid="gn",
            first_member_only=first_member_only,
            generate_xmls=generate_xmls,
            xmls_dir=xmls_dir,
            xml_cmds_sh=xml_cmds_sh,
            generate_ymls=generate_ymls,
            ymls_dir=ymls_dir,
        )  
        models_lf_dict = deep_merge_dicts(models_lf_dict_a, models_lf_dict_o)
        models_dict_combined = deep_merge_dicts(models_dict, models_lf_dict)

    # Save the models_dict to a json file
    output_file = f"models_path_{mip_era}_{exp}_{freq}.json"
    with open(output_file, "w") as f:
        json.dump(models_dict_combined, f, indent=4)
    print(f"Models dictionary saved to {output_file}")


def generate_model_path_dict(
    exp,
    variables,
    freq,
    cmipTable=None,
    mip_era=None,
    grid=None,
    first_member_only=False,
    generate_xmls=False,
    xmls_dir=None,
    xml_cmds_sh=None,
    generate_ymls=False,
    ymls_dir=None,
) -> dict[Any, Any]:
    """
    Generate a dictionary of models and their members with paths to netcdf files.
    """

    # Create a dictionary to hold the models and their members
    # Structure: models_dict[model][member][variable]["path"] = [list of paths to netcdf files]
    models_dict = {}

    for variable in variables:

        # Search all available models
        if grid is None:
            dpaths = xs.findPaths(
                exp, variable, freq, cmipTable=cmipTable, mip_era=mip_era, activity="CMIP"
            )
        else:
            dpaths = xs.findPaths(
                exp, variable, freq, cmipTable=cmipTable, mip_era=mip_era, grid=grid, activity="CMIP"
            )
        models = xs.natural_sort(xs.getGroupValues(dpaths, "model"))

        print("\nSearching for data with xsearch...")
        print("variable:", variable)
        print("mip_era:", mip_era)
        print("exp:", exp)
        print("models:", models)
        print("number of models:", len(models))

        for model in models:

            if model not in models_dict:
                models_dict[model] = {}

            dpaths_model = xs.retainDataByFacetValue(dpaths, "model", model)
            members = xs.natural_sort(xs.getGroupValues(dpaths_model, "member"))

            if first_member_only:
                members = members[0:1]

            # print(model, members)
            for member in members:

                if member not in models_dict[model]:
                    models_dict[model][member] = {}
                if variable not in models_dict[model][member]:
                    models_dict[model][member][variable] = {}

                dpaths_model_member_list = xs.getValuesForFacet(
                    dpaths_model, "member", member
                )
                if len(dpaths_model_member_list) > 1:
                    print(
                        "Error: multiple paths detected for ",
                        model,
                        member,
                        ": ",
                        dpaths_model_member_list,
                    )
                else:
                    dpath = dpaths_model_member_list[0]
                    ncfiles = xs.natural_sort(glob.glob(os.path.join(dpath, "*.nc")))

                    models_dict[model][member][variable]["path"] = ncfiles

                    if generate_xmls:
                        # generate xml file for the variable
                        xml_filename = (
                            f"{mip_era}_{exp}_{model}_{member}_{freq}_{variable}.xml"
                        )
                        xml_filepath = os.path.join(
                            xmls_dir, mip_era, exp, freq, variable, xml_filename
                        )
                        os.makedirs(os.path.dirname(xml_filepath), exist_ok=True)
                        subprocess_args = [
                            "cdscan",
                            "-x",
                            xml_filepath,
                            os.path.join(dpath, "*.nc"),
                        ]
                        # Save the xml generation command to a shell script file
                        if xml_cmds_sh is not None:
                            with open(xml_cmds_sh, "a") as f:
                                f.write(" ".join(subprocess_args) + "\n")

                    if generate_ymls:
                        # generate yml file for the variable
                        yml_filename = (
                            f"{mip_era}_{exp}_{model}_{member}_{freq}_{variable}.yml"
                        )
                        yml_filepath = os.path.join(
                            ymls_dir, mip_era, exp, freq, variable, yml_filename
                        )
                        os.makedirs(os.path.dirname(yml_filepath), exist_ok=True)
                        with open(yml_filepath, "w") as f:
                            f.write(f"directory_path: {dpath}\n")
                            f.write("netcdf_files:\n")
                            for ncfile in ncfiles:
                                f.write(f"  - {os.path.basename(ncfile)}\n")

    return models_dict


def deep_merge_dicts(d1, d2):
    result = d1.copy()
    for key, value in d2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


if __name__ == "__main__":
    main()
