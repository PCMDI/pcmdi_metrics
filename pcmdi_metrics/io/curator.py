import glob
import json
import os
import sys

from pcmdi_metrics.io import xcdat_open


def replace_multi(string, kwdict):
    # Replace multiple keyworks in a string template
    # based on key-value pairs in 'rdict'.
    for k in kwdict.keys():
        string = string.replace(k, kwdict[k])
    return string


def load_ds_from_catalog(cat_dict, variable, model, run, kwargs={}):
    # Load a dataset from file using the information in the catalog
    tags = {
        "%(variable)": variable,
        "%(model)": model,
        "%(model_version)": model,
        "%(realization)": run,
    }
    filename_template = cat_dict[variable][model][run]["filename_template"]
    filenames = glob.glob(replace_multi(filename_template, tags))
    ds = xcdat_open(filenames, **kwargs)
    return ds


# -------------------------------------
# JSON catalog specific functions
# -------------------------------------
def get_filenames_from_json(filename, variable, model, run):
    # Given a filepath that points to a JSON catalog, pull out a single filepath
    with open(filename, "r") as fjson:
        json_dict = json.load(fjson)
    tags = {
        "%(variable)": variable,
        "%(model)": model,
        "%(model_version)": model,
        "%(realization)": run,
    }
    filename_template = json_dict[variable][model][run]["filename_template"]
    filenames = glob.glob(replace_multi(filename_template, tags))
    return filenames


def load_catalog_from_json(filename):
    # TODO: If error, should this return empty dict or exit?
    try:
        with open(filename, "r") as fjson:
            json_dict = json.load(fjson)
    except Exception as e:
        print("ERROR:", e)
        print("Could not load catalog from JSON. See error message above.")
        print("Returning empty dictionary.")
        json_dict = {}
    return json_dict


# -------------------------------------
# Filename template specific functions
# -------------------------------------


def realizations_for_model(filename_template, tags):
    # If realizations is a wildcard, glob the filename template
    # to get the list of realizations available
    if "%(realization)" not in filename_template:
        print("String %(realization) not in filename template")
        return

    # First assume that the realizations each have unique directories
    # Eg
    # model/
    #   r1i1p1f1/
    #        r1i1p1f1.nc
    #   r2i1p1f1/
    #        r2i1p1f1.nc
    fsplit = filename_template.split("/")
    if "%(realization)" in fsplit:
        rpos = fsplit.index("%(realization)")
        filenames = replace_multi(filename_template, tags)
        filenames = "/".join(filenames.split("/")[0:rpos])
        ncfiles = glob.glob(os.path.join(filenames, "*"))
        realizations = [x.split("/")[rpos] for x in ncfiles]
    # Otherwise, they are assumed to be saved together
    # E.g.
    # model/
    #   r1i1p1f1.nc
    #   r2i1p1f1.nc
    else:
        # Note: this logic only works if there are no wildcards in file name
        if "*" not in filename_template:
            # Get the lengths of the str segments surrounding the
            # realization tag, and use those to snip out the realizations
            fullpath0 = replace_multi(filename_template, tags)
            base = os.path.basename(filename_template)
            tags.pop("%(realization)")
            base1 = replace_multi(base, tags)
            fullpath1 = os.path.join(os.path.dirname(fullpath0), base1)
            seg0, seg1 = fullpath1.split("%(realization)")
            l0, l1 = (len(seg0), len(seg1))
            filelist = glob.glob(fullpath0)
            realizations = []
            for f in filelist:
                real = f[l0:-l1]
                if real not in realizations:
                    realizations.append(real)
        else:
            print("Cannot parse realizations from filename template")
            # TODO: Throw error?
            return
    return realizations


def build_catalog_from_template(filename_template, vars_dict):
    # Take the PMP filename template, and return a dictionary
    # that matches the structure of a catalog from JSON.
    # filename_template is a full file path following PMP template rules
    # vars_dict must contain entries for
    # "variables", "models", and "realizations".
    # Does not fail gracefully if vars_dict is missing entries
    # or file path is incorrect
    cat_dict = {}
    for varname in vars_dict["variables"]:
        cat_dict[varname] = {}
        for model in vars_dict["models"]:
            cat_dict[varname][model] = {}
            realization_list = []
            if vars_dict["realizations"]:
                if vars_dict["realizations"][0] == "*":
                    print("finding all realizations")
                    tags = {
                        "%(variable)": varname,
                        "%(model)": model,
                        "%(model_version)": model,
                        "%(realization)": "*",
                    }
                    print(tags)
                    realization_list = realizations_for_model(filename_template, tags)
                    if not realization_list:  # check empty list
                        print("No realizations found.")
                        print("File path may not be valid.")
                        sys.exit()
                else:
                    realization_list = vars_dict["realizations"]
            for run in realization_list:
                tags = {
                    "%(variable)": varname,
                    "%(model)": model,
                    "%(model_version)": model,
                    "%(realization)": run,
                }
                filename = replace_multi(filename_template, tags)
                cat_dict[varname][model][run] = {
                    "CMIP_CMOR_TABLE": "",
                    "MD5sum": "",
                    "RefName": "",
                    "RefTracingDate": "",
                    "filename": os.path.basename(filename),
                    "period": "",
                    "shape": "",
                    "template": filename,
                    "varin": varname,
                }
    return cat_dict
