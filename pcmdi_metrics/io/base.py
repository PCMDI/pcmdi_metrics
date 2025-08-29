import copy
import hashlib
import json
import logging
import os
import re
import shlex
import sys
from collections import OrderedDict
from collections.abc import Mapping
from datetime import datetime
from subprocess import PIPE, Popen

import cdp.cdp_io
import numpy
import requests

import pcmdi_metrics
from pcmdi_metrics import LOG_LEVEL
from pcmdi_metrics.io import StringConstructor

logging.getLogger("pcmdi_metrics").setLevel(LOG_LEVEL)  # set up to log errors

# compatibility check for Python2 (basestring) and Python3 (str)
try:
    basestring  # noqa
except Exception:
    basestring = str


# gather virtual env info
def _determine_conda():
    """
    Attempt to determine the path to the conda executable
    """
    # Begin by checking if user has forced a specific conda executable
    override_conda_exe = os.environ.get("PCMDI_CONDA_EXE")
    if override_conda_exe:
        return override_conda_exe

    # Next check if we are in a conda environment
    conda_python_exe = os.environ.get("CONDA_PYTHON_EXE", "")
    if conda_python_exe != "":
        conda_exe = os.path.join(os.path.dirname(conda_python_exe), "conda")
    else:
        # Fall back to assuming conda is in the PATH
        conda_exe = "conda"

    return conda_exe


CONDA = _determine_conda()

# ----------
# Standalone functions
# ----------


def download_sample_data_files(files_md5, path):
    """Downloads sample data from a list of files"""
    if not os.path.exists(files_md5) or os.path.isdir(files_md5):
        raise RuntimeError("Invalid file type for list of files: %s" % files_md5)
    samples = open(files_md5).readlines()
    download_url_root = samples[0].strip()
    for sample in samples[1:]:
        good_md5, name = sample.split()
        local_filename = os.path.join(path, name)
        try:
            os.makedirs(os.path.dirname(local_filename))
        except BaseException:
            pass
        attempts = 0
        while attempts < 3:
            md5 = hashlib.md5()
            if os.path.exists(local_filename):
                f = open(local_filename, "rb")
                md5.update(f.read())
                if md5.hexdigest() == good_md5:
                    attempts = 5
                    continue
            print(
                "Downloading: '%s' from '%s' in: %s"
                % (name, download_url_root, local_filename)
            )
            r = requests.get("%s/%s" % (download_url_root, name), stream=True)
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter local_filename keep-alive new chunks
                        f.write(chunk)
                        md5.update(chunk)
            f.close()
            if md5.hexdigest() == good_md5:
                attempts = 5
            else:
                attempts += 1
    return


def populate_prov(prov, cmd, pairs, sep=None, index=1, fill_missing=False):
    try:
        p = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    except Exception:
        return
    out, stde = p.communicate()
    if stde.decode("utf-8") != "":
        return
    for strBit in out.decode("utf-8").splitlines():
        for key, value in pairs.items():
            if value in strBit:
                prov[key] = strBit.split(sep)[index].strip()
    if fill_missing is not False:
        for k in pairs:
            if k not in prov:
                prov[k] = fill_missing
    return


def generateProvenance(extra_pairs={}, history=True):
    """Generates provenance info for PMP
    extra_pairs is a dictionary of format: {"name_in_provenance_list" : "python_package"}
    """
    prov = OrderedDict()
    platform = os.uname()
    platfrm = OrderedDict()
    platfrm["OS"] = platform[0]
    platfrm["Version"] = platform[2]
    platfrm["Name"] = platform[1]
    prov["platform"] = platfrm
    try:
        logname = os.getlogin()
    except Exception:
        try:
            import pwd

            logname = pwd.getpwuid(os.getuid())[0]
        except Exception:
            try:
                logname = os.environ.get("LOGNAME", "unknown")
            except Exception:
                logname = "unknown-loginname"
    prov["userId"] = logname
    prov["osAccess"] = bool(os.access("/", os.W_OK) * os.access("/", os.R_OK))
    prov["commandLine"] = " ".join(sys.argv)
    prov["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prov["conda"] = OrderedDict()
    pairs = {
        "Platform": "platform ",
        "Version": "conda version ",
        "IsPrivate": "conda is private ",
        "envVersion": "conda-env version ",
        "buildVersion": "conda-build version ",
        "PythonVersion": "python version ",
        "RootEnvironment": "root environment ",
        "DefaultEnvironment": "default environment ",
    }
    populate_prov(prov["conda"], CONDA + " info", pairs, sep=":", index=-1)
    pairs = {
        "cdp": "cdp ",
        "cdat_info": "cdat_info ",
        # "cdms": "cdms2 ",
        # "cdtime": "cdtime ",
        # "cdutil": "cdutil ",
        "esmf": "esmf ",
        "esmpy": "esmpy ",
        "matplotlib": "matplotlib-base ",
        "numpy": "numpy ",
        "python": "python ",
        "scipy": "scipy ",
        "xcdat": "xcdat ",
        "xarray": "xarray ",
    }
    # Actual environement used
    p = Popen(shlex.split(CONDA + " env export"), stdout=PIPE, stderr=PIPE)
    o, e = p.communicate()
    prov["conda"]["yaml"] = o.decode("utf-8")
    prov["packages"] = OrderedDict()
    populate_prov(prov["packages"], CONDA + " list", pairs, fill_missing=None)
    populate_prov(prov["packages"], CONDA + " list", extra_pairs, fill_missing=None)
    # Trying to capture glxinfo
    pairs = {
        "vendor": "OpenGL vendor string",
        "renderer": "OpenGL renderer string",
        "version": "OpenGL version string",
        "shading language version": "OpenGL shading language version string",
    }
    prov["openGL"] = OrderedDict()
    populate_prov(prov["openGL"], "glxinfo", pairs, sep=":", index=-1)
    prov["openGL"]["GLX"] = {"server": OrderedDict(), "client": OrderedDict()}
    pairs = {
        "version": "GLX version",
    }
    populate_prov(prov["openGL"]["GLX"], "glxinfo", pairs, sep=":", index=-1)
    pairs = {
        "vendor": "server glx vendor string",
        "version": "server glx version string",
    }
    populate_prov(prov["openGL"]["GLX"]["server"], "glxinfo", pairs, sep=":", index=-1)
    pairs = {
        "vendor": "client glx vendor string",
        "version": "client glx version string",
    }
    populate_prov(prov["openGL"]["GLX"]["client"], "glxinfo", pairs, sep=":", index=-1)

    prov["packages"]["PMP"] = pcmdi_metrics.version
    prov["packages"][
        "PMPObs"
    ] = "See 'References' key below, for detailed obs provenance information."

    # Now the history if requested
    if history:
        session_history = ""
        try:
            import IPython

            profile_hist = IPython.core.history.HistoryAccessor()
            session = profile_hist.get_last_session_id()
            cursor = profile_hist.get_range(session)
            for session_id, line, cmd in cursor.fetchall():
                session_history += "{}\n".format(cmd)
            if session_history == "":  # empty history
                # trying to force fallback on readline
                raise
        except Exception:
            # Fallback but does not seem to always work
            import readline

            for i in range(readline.get_current_history_length()):
                session_history += "{}\n".format(readline.get_history_item(i + 1))
            pass
        try:
            import __main__

            with open(__main__.__file__) as f:
                script = f.read()
            prov["script"] = script
        except Exception:
            pass
        prov["history"] = session_history
    return prov


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            r = update_dict(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def sort_human(input_list):
    lst = copy.copy(input_list)

    def convert(text):
        return int(text) if text.isdigit() else text

    def alphanum(key):
        return [convert(c) for c in re.split("([0-9]+)", key)]

    lst.sort(key=alphanum)
    return lst


# ----------
# Base
# ----------


class Base(cdp.cdp_io.CDPIO, StringConstructor):
    def __init__(self, root, file_template, file_mask_template=None):
        StringConstructor.__init__(self, root + "/" + file_template)
        self.root = root
        self.type = ""

    def __call__(self):
        path = os.path.abspath(StringConstructor.__call__(self))
        if self.type in path:
            return path
        else:
            return path + "." + self.type

    def read(self):
        pass

    def write(
        self,
        data,
        type="json",
        mode="w",
        include_YAML=False,
        include_history=False,
        include_script=False,
        include_provenance=True,
        *args,
        **kwargs,
    ):
        self.type = type.lower()
        file_name = self()
        dir_path = os.path.split(file_name)[0]

        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception:
                logging.getLogger("pcmdi_metrics").error(
                    "Could not create output directory: %s" % dir_path
                )

        if self.type == "json":
            json_structure = kwargs.get(
                "json_structure", data.get("json_structure", None)
            )

            for k in ["json_structure"]:
                if k in kwargs:
                    del kwargs[k]
            data["json_structure"] = json_structure

            if mode == "r+" and os.path.exists(file_name):
                f = open(file_name)
                out_dict = json.load(f)
            else:
                if include_provenance:
                    out_dict = OrderedDict({"provenance": generateProvenance()})
                else:
                    out_dict = OrderedDict({"provenance": dict()})
            f = open(file_name, "w")
            update_dict(out_dict, data)
            if "conda" in out_dict["provenance"]:
                if "yaml" in out_dict["provenance"]["conda"]:
                    if include_YAML:
                        out_dict["YAML"] = out_dict["provenance"]["conda"]["yaml"]
                    del out_dict["provenance"]["conda"]["yaml"]

            if not include_script:
                if "script" in out_dict["provenance"].keys():
                    del out_dict["provenance"]["script"]

            if not include_history:
                if "history" in out_dict["provenance"].keys():
                    del out_dict["provenance"]["history"]

            json.dump(out_dict, f, *args, **kwargs)
            f.close()

        logging.getLogger("pcmdi_metrics").info(
            "Results saved to a %s file: %s" % (type, file_name)
        )

    def write_cmec(self, *args, **kwargs):
        """Converts a json file to cmec compliant format."""

        file_name = self()
        try:
            f = open(file_name, "r")
            data = json.load(f)
            f.close()
        except Exception:
            logging.getLogger("pcmdi_metrics").error(
                "Could not load metrics file: %s" % file_name
            )

        # create dimensions
        cmec_data = {"DIMENSIONS": {}, "SCHEMA": {}}
        cmec_data["DIMENSIONS"] = {"json_structure": []}
        cmec_data["SCHEMA"] = {"name": "CMEC", "package": "PMP", "version": "v1"}

        # copy other fields except results
        for key in data:
            if key not in ["json_structure", "RESULTS"]:
                cmec_data[key] = data[key]

        # move json structure
        cmec_data["DIMENSIONS"]["json_structure"] = data["json_structure"]

        # recursively process json
        def recursive_replace(json_dict, extra_fields):
            new_dict = json_dict.copy()
            # replace blank keys with unspecified
            if "" in new_dict:
                new_dict["Unspecified"] = new_dict.pop("")

            for key in new_dict:
                if key != "attributes":
                    if isinstance(new_dict[key], dict):
                        # move extra fields into attributes key
                        atts = {}
                        for field in extra_fields:
                            if field in new_dict[key]:
                                atts[field] = new_dict[key].pop(field, None)
                        if atts:
                            new_dict[key]["attributes"] = atts
                        # process sub-dictionary
                        tmp_dict = recursive_replace(new_dict[key], extra_fields)
                        new_dict[key] = tmp_dict
                    # convert string metrics to float or None
                    if isinstance(new_dict[key], str):
                        if new_dict[key] == "NaN":
                            new_dict[key] = None
                        else:
                            new_dict[key] = float(new_dict[key])
                    # convert NaN to None
                    elif not isinstance(new_dict[key], dict):
                        if not isinstance(new_dict[key], list):
                            if numpy.isnan(new_dict[key]):
                                new_dict[key] = None
            return new_dict

        extra_fields = [
            "source",
            "metadata",
            "units",
            "SimulationDescription",
            "InputClimatologyFileName",
            "InputClimatologyMD5",
            "InputRegionFileName",
            "InputRegionMD5",
            "best_matching_model_eofs__cor",
            "best_matching_model_eofs__rms",
            "best_matching_model_eofs__tcor_cbf_vs_eof_pc",
            "period",
            "target_model_eofs",
            "analysis_time_window_end_year",
            "analysis_time_window_start_year",
        ]
        # clean up formatting in RESULTS section
        cmec_data["RESULTS"] = recursive_replace(data["RESULTS"], extra_fields)

        # Populate dimensions fields
        def get_dimensions(json_dict, json_structure):
            keylist = {}
            level = 0
            while level < len(json_structure):
                if isinstance(json_dict, dict):
                    first_key = list(json_dict.items())[0][0]
                    # skip over attributes key when building dimensions
                    if first_key == "attributes":
                        first_key = list(json_dict.items())[1][0]
                    dim = json_structure[level]
                    keys = {key: {} for key in json_dict if key != "attributes"}
                    keylist[dim] = keys
                    json_dict = json_dict[first_key]
                level += 1
            return keylist

        dimensions = get_dimensions(cmec_data["RESULTS"].copy(), data["json_structure"])
        cmec_data["DIMENSIONS"].update(dimensions)

        cmec_file_name = file_name.replace(".json", "_cmec.json")
        f_cmec = open(cmec_file_name, "w")

        json.dump(cmec_data, f_cmec, *args, **kwargs)
        f_cmec.close()

        logging.getLogger("pcmdi_metrics").info(
            "CMEC results saved to a %s file: %s" % ("json", cmec_file_name)
        )
