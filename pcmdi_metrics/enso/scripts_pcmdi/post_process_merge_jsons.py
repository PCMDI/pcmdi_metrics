#!/usr/bin/env python

from __future__ import print_function
from genutil import StringConstructor
from pcmdi_metrics.variability_mode.lib import dict_merge

import copy
import glob
import json
import os


def main():
    # mips = ["cmip5", "cmip6"]
    # mips = ["cmip5"]
    mips = ["cmip6"]
    # mips = ["obs2obs"]
    # mips = ["CLIVAR_LE"]

    exps = ["historical"]

    # MCs = ["ENSO_perf", "ENSO_tel", "ENSO_proc", "test_tel"]
    MCs = ["ENSO_perf", "ENSO_tel", "ENSO_proc"]
    # MCs = ["ENSO_tel"]
    # MCs = ["test_tel"]

    pmprdir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2'
    # pmprdir = "/work/lee1043/imsi/result_test"

    for mip in mips:
        for exp in exps:
            for MC in MCs:
                case_id = find_latest(pmprdir, mip, exp, MC)
                print("mip, exp, MC, case_id:", mip, exp, MC, case_id)
                merge_jsons(mip, exp, case_id, MC, pmprdir)


def merge_jsons(mip, exp, case_id, metricsCollection, pmprdir):
    json_file_dir_template = os.path.join(
        pmprdir,
        '%(output_type)', 'enso_metric',
        '%(mip)', '%(exp)', '%(case_id)', '%(metricsCollection)')
    json_file_dir_template = StringConstructor(json_file_dir_template)
    json_file_dir = json_file_dir_template(
        output_type='metrics_results', mip=mip, exp=exp, case_id=case_id, metricsCollection=metricsCollection)

    json_file_template = '_'.join(['%(mip)_%(exp)_%(metricsCollection)', '%(case_id)', '%(model)', '%(realization)'])
    json_file_template = '%(mip)_%(exp)_%(metricsCollection)_%(case_id)_%(model)_%(realization)'
    json_file_template = StringConstructor(json_file_template)

    # Search for individual JSONs
    json_files = sorted(glob.glob(
        os.path.join(
            json_file_dir,
            json_file_template(
                mip=mip, exp=exp, metricsCollection=metricsCollection,
                case_id=case_id, model='*', realization='*') + '.json')))

    # Remove diveDown JSONs and previously generated merged JSONs if included
    json_files_revised = copy.copy(json_files)
    for j, json_file in enumerate(json_files):
        filename_component = json_file.split('/')[-1].split('.')[0].split('_')
        if 'diveDown' in filename_component:
            json_files_revised.remove(json_file)
        elif 'allModels' in filename_component:
            json_files_revised.remove(json_file)
        elif 'allRuns' in filename_component:
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
    final_json_filename = json_file_template(
        mip=mip, exp=exp, metricsCollection=metricsCollection, case_id=case_id,
        model='allModels', realization='allRuns')+'.json'
    final_json_file = os.path.join(json_file_dir, final_json_filename)

    with open(final_json_file, 'w') as fp:
        json.dump(dict_final, fp, sort_keys=True, indent=4)

    print("Done: check ", final_json_file)


def find_latest(pmprdir, mip, exp, MC):
    versions = sorted([r.split('/')[-2] for r in glob.glob(os.path.join(
                          pmprdir, "metrics_results", "enso_metric",
                          mip, exp, "v????????", MC))])
    latest_version = versions[-1]
    return latest_version


if __name__ == "__main__":
    main()
