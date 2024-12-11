import glob
import json
import os

import xcdat

from pcmdi_metrics.io import xcdat_openxml


def replace_multi(string, kwdict):
    # Replace multiple keyworks in a string template
    # based on key-value pairs in 'rdict'.
    for k in kwdict.keys():
        string = string.replace(k, kwdict[k])
    return string


def fix_calendar(ds):
    cal = ds.time.calendar
    # Add any calendar fixes here
    cal = cal.replace("-", "_")
    ds.time.attrs["calendar"] = cal
    ds = xcdat.decode_time(ds)
    return ds


def load_ds_from_file(infile, load_options={}):
    # TODO: Figure out how to get this into the open_xcdat function.
    # https://github.com/PCMDI/pcmdi_metrics/blob/main/pcmdi_metrics/io/xcdat_openxml.py#L11
    # Load an xarray dataset from the given filepath.
    # If list of netcdf files, opens mfdataset.
    # If list of xmls, open last file in list.
    if isinstance(infile, list) or "*" in infile:
        if infile[-1].endswith(".xml"):
            # Final item of sorted list would have most recent version date
            ds = xcdat_openxml.xcdat_openxml(infile[-1])
        else:
            try:
                ds = xcdat.open_mfdataset(infile, **load_options)
            except ValueError:  # Usually due to calendar issue
                ds = xcdat.open_mfdataset(infile, decode_times=False, **load_options)
                ds = fix_calendar(ds)
    else:  # Single path
        try:
            ds = xcdat.open_dataset(infile, **load_options)
        except ValueError:  # Usually due to calendar issue
            ds = xcdat.open_dataset(infile, decode_times=False, **load_options)
            ds = fix_calendar(ds)
    return ds.bounds.add_missing_bounds()


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
    ds = load_ds_from_file(filenames, **kwargs)
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
    fsplit = filename_template.split("/")
    if "%(realization)" in fsplit:
        rpos = fsplit.index("%(realization)")
        filenames = replace_multi(filename_template, tags)
        filenames = "/".join(filenames.split("/")[0:rpos])
        ncfiles = glob.glob(os.path.join(filenames, "*"))
        realizations = [x.split("/")[rpos] for x in ncfiles]
    # Otherwise, they are assumed to be saved together
    else:
        # How do you deal with wildcard following realization tag?
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
    cat_dict = {}
    for varname in vars_dict["variables"]:
        cat_dict[varname] = {}
        for model in vars_dict["models"]:
            cat_dict[varname][model] = {}
            if vars_dict["realizations"] == "*":
                tags = {
                    "%(variable)": varname,
                    "%(model)": model,
                    "%(model_version)": model,
                    "%(realization)": "*",
                }
                realization_list = realizations_for_model(filename_template, tags)
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
