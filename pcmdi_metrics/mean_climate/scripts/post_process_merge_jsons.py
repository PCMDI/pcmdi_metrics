#!/usr/bin/env python

import copy
import glob
import json
import os

from genutil import StringConstructor

from pcmdi_metrics.variability_mode.lib import dict_merge


def main():
    # mips = ['cmip5', 'cmip6']
    mips = ["cmip6"]
    # mips = ['cmip3']

    # exps = ['historical', 'amip']
    exps = ["historical"]
    # exps = ["amip"]
    # exps = ['20c3m', 'amip']
    # exps = ['20c3m']

    case_id = "v20230202"

    syear = 1900
    eyear = 2005

    obs_selection = "default"
    # obs_selection = 'alternative'

    # pmprdir = '/work/lee1043/temporary/result_test'
    pmprdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"

    for mip in mips:
        for exp in exps:
            variables = [
                s.split("/")[-1]
                for s in glob.glob(
                    os.path.join(
                        pmprdir,
                        "metrics_results",
                        "mean_climate",
                        mip,
                        exp,
                        case_id,
                        "*",
                    )
                )
                if os.path.isdir(s)
            ]
            print("variables:", variables)
            for var in variables:
                # json merge
                # try:
                if 1:
                    merge_json(
                        mip, exp, case_id, var, obs_selection, syear, eyear, pmprdir
                    )
                """
                except Exception as err:
                    print("ERROR: ", mip, exp, var, err)
                    pass
                """


def merge_json(mip, exp, case_id, var, obs, syear, eyear, pmprdir):
    json_file_dir_template = (
        "metrics_results/mean_climate/%(mip)/%(exp)/%(case_id)/%(var)"
    )
    json_file_dir_template = StringConstructor(json_file_dir_template)
    json_file_dir = os.path.join(
        pmprdir,
        json_file_dir_template(mip=mip, exp=exp, case_id=case_id, var=var),
    )

    print("json_file_dir:", json_file_dir)

    json_file_template = "%(model)_%(var)_*_%(obs).json"
    json_file_template = StringConstructor(json_file_template)

    # Search for individual JSONs
    json_files = sorted(
        glob.glob(
            os.path.join(
                json_file_dir,
                json_file_template(
                    # mip=mip,
                    # exp=exp,
                    var=var,
                    model="*",
                    # run="*",
                    obs=obs,
                ),
            )
        )
    )

    print("json_files:", json_files)

    # Remove diveDown JSONs and previously generated merged JSONs if included
    json_files_revised = copy.copy(json_files)
    for j, json_file in enumerate(json_files):
        filename_component = json_file.split("/")[-1].split(".")[0].split("_")
        if "allModels" in filename_component:
            json_files_revised.remove(json_file)
        elif "allRuns" in filename_component:
            json_files_revised.remove(json_file)

    # Load individual JSON and merge to one big dictionary
    for j, json_file in enumerate(json_files_revised):
        print(j, json_file)
        f = open(json_file)
        dict_tmp = json.loads(f.read())
        if j == 0:
            dict_final = dict_tmp.copy()
        else:
            dict_merge(dict_final, dict_tmp)
        f.close()

    # Dump final dictionary to JSON
    final_json_filename = StringConstructor("%(var)_%(mip)_%(exp)_%(case_id).json")(
        var=var, mip=mip, exp=exp, case_id=case_id
    )
    final_json_file = os.path.join(json_file_dir, "..", final_json_filename)

    with open(final_json_file, "w") as fp:
        json.dump(dict_final, fp, sort_keys=True, indent=4)


if __name__ == "__main__":
    main()
