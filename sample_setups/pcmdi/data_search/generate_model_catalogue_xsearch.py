import glob
import json
import os
from typing import Any

import xsearch as xs


def main():
    # User options ------------------------------------------------------------------
    mip_era = "CMIP6"
    exp = "historical"
    variables = ["psl", "ts"]
    freq = "mon"
    cmipTable = "Amon"

    first_member_only = False
    include_lf = True  # include land fraction variable 'sftlf'
    # -------------------------------------------------------------------------------

    generate_model_catalogue_xsearch(
        mip_era=mip_era,
        exp=exp,
        variables=variables,
        freq=freq,
        cmipTable=cmipTable,
        first_member_only=first_member_only,
        include_lf=include_lf,
    )


def generate_model_catalogue_xsearch(
    mip_era: str,
    exp: str,
    variables: list[str],
    freq: str,
    cmipTable: str = None,
    first_member_only: bool = False,
    include_lf: bool = True,
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
        mip_era=mip_era,
        first_member_only=first_member_only,
    )
    models_dict_combined = models_dict

    if include_lf:
        models_lf_dict = generate_model_path_dict(
            exp=exp,
            variables=["sftlf"],
            freq="fx",
            cmipTable="fx",
            mip_era=mip_era,
            first_member_only=first_member_only,
        )
        models_dict_combined = deep_merge_dicts(models_dict, models_lf_dict)

    # Save the models_dict to a json file
    output_file = f"models_path_{mip_era}_{exp}_{freq}.json"
    with open(output_file, "w") as f:
        json.dump(models_dict_combined, f, indent=4)
    print(f"Models dictionary saved to {output_file}")


def generate_model_path_dict(
    exp, variables, freq, cmipTable=None, mip_era=None, first_member_only=False
) -> dict[Any, Any]:
    """
    Generate a dictionary of models and their members with paths to netcdf files.
    """

    # Create a dictionary to hold the models and their members
    # Structure: models_dict[model][member][variable]["path"] = [list of paths to netcdf files]
    models_dict = {}

    for variable in variables:

        # Search all available models
        dpaths = xs.findPaths(exp, variable, freq, cmipTable=cmipTable, mip_era=mip_era)
        models = xs.natural_sort(xs.getGroupValues(dpaths, "model"))

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
