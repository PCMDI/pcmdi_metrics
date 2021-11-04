#!/usr/bin/env python

from __future__ import print_function
from genutil import StringConstructor
from pcmdi_metrics.mjo.lib import dict_merge

import copy
import glob
import json
import os


def main():
    mips = ["cmip5", "cmip6"]
    # mips = ["cmip5"]
    # mips = ["cmip6"]

    exps = ["historical"]

    pmprdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"
    # pmprdir = "/work/lee1043/imsi/result_test"

    for mip in mips:
        for exp in exps:
            case_id = find_latest(pmprdir, mip, exp)
            print("mip, exp, case_id:", mip, exp, case_id)
            merge_jsons(mip, exp, case_id, pmprdir)


def merge_jsons(mip, exp, case_id, pmprdir):
    json_file_dir_template = os.path.join(
        pmprdir, "%(output_type)", "mjo", "%(mip)", "%(exp)", "%(case_id)"
    )
    json_file_dir_template = StringConstructor(json_file_dir_template)
    json_file_dir = json_file_dir_template(
        output_type="metrics_results", mip=mip, exp=exp, case_id=case_id
    )
    print("json_file_dir:", json_file_dir)

    json_file_template = (
        "mjo_stat_%(mip)_%(exp)_da_atm_%(model)_%(realization)_1985-2004"
    )
    json_file_template = StringConstructor(json_file_template)

    # Search for individual JSONs
    json_files = sorted(
        glob.glob(
            os.path.join(
                json_file_dir,
                json_file_template(
                    mip=mip, exp=exp, case_id=case_id, model="*", realization="*"
                )
                + ".json",
            )
        )
    )

    # Remove diveDown JSONs and previously generated merged JSONs if included
    json_files_revised = copy.copy(json_files)
    for j, json_file in enumerate(json_files):
        filename_component = json_file.split("/")[-1].split(".")[0].split("_")
        if "diveDown" in filename_component:
            json_files_revised.remove(json_file)
        elif "allModels" in filename_component:
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
    final_json_filename = (
        json_file_template(
            mip=mip, exp=exp, case_id=case_id, model="allModels", realization="allRuns"
        )
        + ".json"
    )
    final_json_file = os.path.join(json_file_dir, final_json_filename)
    print("final_json_filename:", final_json_filename)

    with open(final_json_file, "w") as fp:
        json.dump(dict_final, fp, sort_keys=True, indent=4)

    print("Done: check ", final_json_file)


def find_latest(pmprdir, mip, exp):
    versions = sorted(
        [
            r.split("/")[-1]
            for r in glob.glob(
                os.path.join(pmprdir, "metrics_results", "mjo", mip, exp, "v????????")
            )
        ]
    )
    latest_version = versions[-1]
    return latest_version


if __name__ == "__main__":
    main()
