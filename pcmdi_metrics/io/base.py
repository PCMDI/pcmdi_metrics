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

import cdms2
import cdp.cdp_io
import cdutil
import genutil
import MV2
import numpy
import requests
import xcdat
import xcdat as xc

import pcmdi_metrics
from pcmdi_metrics import LOG_LEVEL
from pcmdi_metrics.io import StringConstructor

value = 0
cdms2.setNetcdfShuffleFlag(value)  # where value is either 0 or 1
cdms2.setNetcdfDeflateFlag(value)  # where value is either 0 or 1
# where value is a integer between 0 and 9 included
cdms2.setNetcdfDeflateLevelFlag(value)
logging.getLogger("pcmdi_metrics").setLevel(LOG_LEVEL)

try:
    basestring  # noqa
except Exception:
    basestring = str

CONDA = os.environ.get("CONDA_PYTHON_EXE", "")
if CONDA != "":
    CONDA = os.path.join(os.path.dirname(CONDA), "conda")
else:
    CONDA = "conda"


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
        "cdms": "cdms2 ",
        "cdtime": "cdtime ",
        "cdutil": "cdutil ",
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


# Convert cdms MVs to json
def MV2Json(data, dic={}, struct=None):
    if struct is None:
        struct = []
    if not isinstance(data, cdms2.tvariable.TransientVariable) and dic != {}:
        raise RuntimeError("MV2Json needs a cdms2 transient variable as input")
    if not isinstance(data, cdms2.tvariable.TransientVariable):
        return data, struct  # we reach the end
    else:
        axis = data.getAxis(0)
        if axis.id not in struct:
            struct.append(axis.id)
        for i, name in enumerate(axis):
            dic[name], _ = MV2Json(data[i], {}, struct)
    return dic, struct


# Group merged axes
def groupAxes(axes, ids=None, separator="_"):
    if ids is None:
        ids = [ax.id for ax in axes]
    if len(ids) != len(axes):
        raise RuntimeError("You need to pass as many ids as axes")
    final = []
    while len(axes) > 0:
        axis = axes.pop(-1)
        if final == []:
            final = [str(v) for v in axis]
        else:
            tmp = final
            final = []
            for v1 in axis:
                for v2 in tmp:
                    final += ["{}{}{}".format(v1, separator, v2)]
    return cdms2.createAxis(final, id=separator.join(ids))


# cdutil region object need a serializer
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


def scrap(data, axis=0):
    originalOrder = data.getOrder(ids=True)
    if axis not in ["x", "y", "z", "t"] and not isinstance(axis, int):
        order = "({})...".format(axis)
    else:
        order = "{}...".format(axis)
    new = data(order=order)
    axes = new.getAxisList()  # Save for later
    new = MV2.array(new.asma())  # lose dims
    for i in range(new.shape[0] - 1, -1, -1):
        tmp = new[i]
        if not isinstance(tmp, (float, numpy.float)) and tmp.mask.all():
            a = new[:i]
            b = new[i + 1 :]
            if b.shape[0] == 0:
                new = a
            else:
                new = MV2.concatenate((a, b))
    newAxis = []
    for v in new.getAxis(0):
        newAxis.append(axes[0][int(v)])
    ax = cdms2.createAxis(newAxis, id=axes[0].id)
    axes[0] = ax
    new.setAxisList(axes)
    return new(order=originalOrder)


class CDMSDomainsEncoder(json.JSONEncoder):
    def default(self, o):
        components = o.components()[0].kargs
        args = ",".join(["%s=%s" % (key, val) for key, val in components.items()])
        return {o.id: "cdutil.region.domain(%s)" % args}


class Base(cdp.cdp_io.CDPIO, StringConstructor):
    def __init__(self, root, file_template, file_mask_template=None):
        StringConstructor.__init__(self, root + "/" + file_template)
        self.target_grid = None
        self.mask = None
        self.target_mask = None
        self.regrid_tool = "esmf"
        self.file_mask_template = file_mask_template
        self.root = root
        self.type = ""
        self.setup_cdms2()

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
            json_version = float(
                kwargs.get("json_version", data.get("json_version", 3.0))
            )
            json_structure = kwargs.get(
                "json_structure", data.get("json_structure", None)
            )
            if json_version >= 3.0 and json_structure is None:
                raise Exception(
                    "json_version 3.0 of PMP requires json_structure to be passed"
                    + "to the write function or part of the dictionary dumped"
                )
            for k in ["json_structure", "json_version"]:
                if k in kwargs:
                    del kwargs[k]
            data["json_version"] = json_version
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

            json.dump(out_dict, f, cls=CDMSDomainsEncoder, *args, **kwargs)
            f.close()

        elif self.type in ["asc", "ascii", "txt"]:
            f = open(file_name, "w")
            for key in list(data.keys()):
                f.write("%s %s\n" % (key, data[key]))
            f.close()

        elif self.type == "nc":
            data.to_netcdf(file_name)

        else:
            logging.getLogger("pcmdi_metrics").error("Unknown type: %s" % type)
            raise RuntimeError("Unknown type: %s" % type)

        logging.getLogger("pcmdi_metrics").info(
            "Results saved to a %s file: %s" % (type, file_name)
        )

    def write_cmec(self, *args, **kwargs):
        """Converts json file to cmec compliant format."""

        file_name = self()
        # load json file
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
        json.dump(cmec_data, f_cmec, cls=CDMSDomainsEncoder, *args, **kwargs)
        f_cmec.close()
        logging.getLogger("pcmdi_metrics").info(
            "CMEC results saved to a %s file: %s" % ("json", cmec_file_name)
        )

    def get(self, var, var_in_file=None, region={}, *args, **kwargs):
        self.variable = var
        self.var_from_file = self.extract_var_from_file(
            var, var_in_file, *args, **kwargs
        )

        self.region = region
        if self.region is None:
            self.region = {}
        self.value = self.region.get("value", None)

        if self.is_masking():
            self.var_from_file = self.mask_var(self.var_from_file)

        self.var_from_file = self.set_target_grid_and_mask_in_var(
            self.var_from_file, var
        )

        self.var_from_file = self.set_domain_in_var(self.var_from_file, self.region)

        return self.var_from_file

    def extract_var_from_file(self, var, var_in_file, *args, **kwargs):
        if var_in_file is None:
            var_in_file = var

        try:
            ds = xc.open_mfdataset(self(), data_var=var_in_file, decode_times=True)
        except Exception:
            ds = xc.open_mfdataset(
                self(), data_var=var_in_file, decode_times=False
            )  # Temporary part to read in cdms written obs4MIP AC files

        if "level" in list(kwargs.keys()):
            level = kwargs["level"]
            ds = ds.sel(plev=level)

        extracted_var = ds

        return extracted_var

    def is_masking(self):
        if self.value is not None:
            return True
        else:
            return False

    def mask_var(self, var):
        """
        self: <pcmdi_metrics.io.base.Base object at 0x7f24a0768a60>
        var: <xarray.Dataset>
        """
        var_shape = tuple(var.dims[d] for d in ["lat", "lon"])

        if self.mask is None:
            self.set_file_mask_template()
            self.mask = self.get_mask_from_var(var)
        # if self.mask.shape != var.shape:
        if self.mask.shape != var_shape:
            dummy, mask = genutil.grower(var, self.mask)
        else:
            mask = self.target_mask
        mask = MV2.not_equal(mask, self.value)
        return MV2.masked_where(mask, var)

    def set_target_grid_and_mask_in_var(self, var, var_in_file):
        """
        self: <class 'pcmdi_metrics.io.base.Base'> object
        self(): string, path to input file
        """
        if self.target_grid is not None:
            var = var.regridder.horizontal(
                var_in_file, self.target_grid, tool=self.regrid_tool
            )
            if self.target_mask is not None:
                # if self.target_mask.shape != var.shape:
                if self.target_mask.shape != var[var_in_file].shape:
                    dummy, mask = genutil.grower(var, self.target_mask)
                else:
                    mask = self.target_mask
                var = MV2.masked_where(mask, var)
        return var

    def set_domain_in_var(self, var, region):
        """
        self: <class 'pcmdi_metrics.io.base.Base'>
        var: <xarray.Dataset>
        region: <class 'dict'>, e.g., {'domain': Selector(<cdutil.region.DomainComponent object at 0x7fdbe2b70760>), 'id': 'NHEX'}
        """
        region_id = region["id"]
        from pcmdi_metrics.io import load_regions_specs, region_subset

        regions_specs = load_regions_specs()
        if region_id not in ["global", "land", "ocean"]:
            var = region_subset(var, regions_specs, region=region_id)

        return var

    def set_file_mask_template(self):
        if isinstance(self.file_mask_template, basestring):
            self.file_mask_template = Base(
                self.root,
                self.file_mask_template,
                {"domain": self.region.get("domain", None)},
            )

    def get_mask_from_var(self, var):
        try:
            # o_mask = self.file_mask_template.get("sftlf")
            o_mask = self.file_mask_template.get("sftlf", var_in_file="sftlf")
        except Exception:
            o_mask = (
                cdutil.generateLandSeaMask(var, regridTool=self.regrid_tool).filled(1.0)
                * 100.0
            )
            o_mask = MV2.array(o_mask)
            o_mask.setAxis(-1, var.getLongitude())
            o_mask.setAxis(-2, var.getLatitude())
        return o_mask

    def set_target_grid(self, target, regrid_tool="esmf", regrid_method="linear"):
        self.regrid_tool = regrid_tool
        self.regrid_method = regrid_method
        if target == "2.5x2.5":
            # self.target_grid = cdms2.createUniformGrid(-88.875, 72, 2.5, 0, 144, 2.5)
            self.target_grid = xcdat.create_uniform_grid(
                -88.875, 88.625, 2.5, 0, 357.5, 2.5
            )
            self.target_grid_name = target
        elif cdms2.isGrid(target):
            self.target_grid = target
            self.target_grid_name = target
        else:
            logging.getLogger("pcmdi_metrics").error("Unknown grid: %s" % target)
            raise RuntimeError("Unknown grid: %s" % target)

    def setup_cdms2(self):
        cdms2.setNetcdfShuffleFlag(0)  # Argument is either 0 or 1
        cdms2.setNetcdfDeflateFlag(0)  # Argument is either 0 or 1
        cdms2.setNetcdfDeflateLevelFlag(0)  # Argument is int between 0 and 9

    def hash(self, block_size=65536):
        self_file = open(self(), "rb")
        buffer = self_file.read(block_size)
        hasher = hashlib.md5()
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = self_file.read(block_size)
        self_file.close()
        return hasher.hexdigest()


class JSONs(object):
    def addDict2Self(self, json_dict, json_struct, json_version):
        if float(json_version) == 1.0:
            V = json_dict[list(json_dict.keys())[0]]
            for model in list(V.keys()):  # loop through models
                m = V[model]
                for ref in list(m.keys()):
                    aref = m[ref]
                    if not (
                        isinstance(aref, dict) and "source" in aref
                    ):  # not an obs key
                        continue
                    reals = list(aref.keys())
                    src = reals.pop(reals.index("source"))
                    for real in reals:
                        areal = aref[real]
                        areal2 = {"source": src}
                        for region in list(areal.keys()):
                            reg = areal[region]
                            if region == "global":
                                region2 = ""
                            else:
                                region2 = region + "_"
                            areal2[region2 + "global"] = {}
                            areal2[region2 + "NHEX"] = {}
                            areal2[region2 + "SHEX"] = {}
                            areal2[region2 + "TROPICS"] = {}
                            key_stats = list(reg.keys())
                            for k in key_stats:
                                if k[:7] == "custom_":
                                    continue
                                else:
                                    sp = k.split("_")
                                    new_key = "_".join(sp[:-1])
                                    domain = sp[-1]
                                    if domain == "GLB":
                                        domain = "global"
                                    sp = new_key.split("_")
                                    stat = "_".join(sp[:-1])
                                    stat_dict = areal2[region2 + domain].get(stat, {})
                                    season = sp[-1]
                                    season_dict = stat_dict
                                    stat_dict[season] = reg[k]
                                    if stat in areal2[region2 + domain]:
                                        areal2[region2 + domain][stat].update(stat_dict)
                                    else:
                                        areal2[region2 + domain][stat] = stat_dict
                        # Now we can replace the realization with the correctly
                        # formatted one
                        aref[real] = areal2
                    # restore ref into model
                    m[ref] = aref
        elif float(json_version) == 2.0:
            V = json_dict[list(json_dict.keys())[0]]
            for model in list(V.keys()):  # loop through models
                m = V[model]
                for ref in list(m.keys()):
                    aref = m[ref]
                    if not (
                        isinstance(aref, dict) and "source" in aref
                    ):  # not an obs key
                        continue
                    reals = list(aref.keys())
                    src = reals.pop(reals.index("source"))
                    for real in reals:
                        areal = aref[real]
                        for region in list(areal.keys()):
                            reg = areal[region]
                            key_stats = list(reg.keys())
                            for k in key_stats:
                                if k[:7] == "custom_":
                                    continue
                                sp = k.split("_")
                                season = sp[-1]
                                stat = "_".join(sp[:-1])
                                stat_dict = reg.get(stat, {})
                                season_dict = stat_dict.get(season, {})
                                season_dict[season] = reg[k]
                                # if stat_dict.has_key(stat):
                                #    stat_dict[stat].update(season_dict)
                                # else:
                                #    stat_dict[stat]=season_dict
                                del reg[k]
                                if stat in reg:
                                    reg[stat].update(season_dict)
                                else:
                                    reg[stat] = season_dict
                        aref[real] = areal
                    # restore ref into model
                    m[ref] = aref
                V[model] = m
            json_dict[list(json_dict.keys())[0]] = V
        update_dict(self.data, json_dict)

    def get_axes_values_recursive(self, depth, max_depth, data, values):
        for k in list(data.keys()):
            if k not in self.ignored_keys and (
                isinstance(data[k], dict) or depth == max_depth
            ):
                values[depth].add(k)
                if depth != max_depth:
                    self.get_axes_values_recursive(
                        depth + 1, max_depth, data[k], values
                    )

    def get_array_values_from_dict_recursive(self, out, ids, nms, axval, axes):
        if len(axes) > 0:
            for i, val in enumerate(axes[0][:]):
                self.get_array_values_from_dict_recursive(
                    out,
                    list(ids)
                    + [
                        i,
                    ],
                    list(nms) + [axes[0].id],
                    list(axval)
                    + [
                        val,
                    ],
                    axes[1:],
                )
        else:
            vals = self.data
            for k in axval:
                try:
                    vals = vals[k]
                except Exception:
                    vals = 9.99e20
            try:
                out[tuple(ids)] = float(vals)
            except Exception:
                out[tuple(ids)] = 9.99e20

    def __init__(
        self,
        files=[],
        structure=[],
        ignored_keys=[],
        oneVariablePerFile=True,
        sortHuman=True,
    ):
        self.json_version = 3.0
        self.json_struct = structure
        self.data = {}
        self.axes = None
        self.ignored_keys = ignored_keys
        self.oneVariablePerFile = oneVariablePerFile
        self.sortHuman = sortHuman
        if len(files) == 0:
            raise Exception("You need to pass at least one file")

        for fnm in files:
            self.addJson(fnm)

    def addJson(self, filename):
        f = open(filename)
        tmp_dict = json.load(f)
        json_struct = tmp_dict.get("json_structure", list(self.json_struct))
        json_version = tmp_dict.get("json_version", self.json_version)
        if self.oneVariablePerFile and json_struct[0] == "variable":
            json_struct = json_struct[1:]
        if self.oneVariablePerFile and json_struct[0] != "variable":
            json_struct.insert(0, "variable")
            var = tmp_dict.get("Variable", None)
            if var is None:  # Not stored in json, need to get from file name
                fnm = os.path.basename(filename)
                varnm = fnm.split("_")[0]
            else:
                varnm = var["id"]
                if "level" in var:
                    varnm += "-%i" % int(var["level"] / 100.0)
            tmp_dict = {varnm: tmp_dict["RESULTS"]}
        else:
            tmp_dict = tmp_dict["RESULTS"]
        if json_struct != self.json_struct and self.json_struct == []:
            self.json_struct = json_struct
        self.addDict2Self(tmp_dict, json_struct, json_version)

    def getAxis(self, axis):
        axes = self.getAxisList()
        for a in axes:
            if a.id == axis:
                return a
        return None

    def getAxisIds(self):
        axes = self.getAxisList()
        return [ax.id for ax in axes]

    def getAxisList(self):
        values = []
        axes = []
        for a in self.json_struct:
            values.append(set())
        self.get_axes_values_recursive(0, len(self.json_struct) - 1, self.data, values)
        autoBounds = cdms2.getAutoBounds()
        cdms2.setAutoBounds("off")
        if self.sortHuman:
            sortFunc = sort_human
        else:
            sortFunc = sorted
        for i, nm in enumerate(self.json_struct):
            axes.append(cdms2.createAxis(sortFunc(list(values[i])), id=nm))
        self.axes = axes
        cdms2.setAutoBounds(autoBounds)
        return self.axes

    def __call__(self, merge=[], **kargs):
        """Returns the array of values"""
        # First clean up kargs
        if "merge" in kargs:
            merge = kargs["merge"]
            del kargs["merge"]
        order = None
        axes_ids = self.getAxisIds()
        if "order" in kargs:
            # If it's an actual axis assume that it's what user wants
            # Otherwise it's an out order keyword
            if "order" not in axes_ids:
                order = kargs["order"]
                del kargs["order"]
        ab = cdms2.getAutoBounds()
        cdms2.setAutoBounds("off")
        axes = self.getAxisList()
        if merge != []:
            if isinstance(merge[0], str):
                merge = [
                    merge,
                ]
        if merge != []:
            for merger in merge:
                for merge_axis_id in merger:
                    if merge_axis_id not in axes_ids:
                        raise RuntimeError(
                            "You requested to merge axis is '{}' which is not valid. Axes: {}".format(
                                merge_axis_id, axes_ids
                            )
                        )
        sh = []
        ids = []
        used_ids = []
        for a in axes:
            # Regular axis not a merged one
            sh.append(len(a))  # store length to construct array shape
            ids.append(a.id)  # store ids

            used_ids.append(a.id)

        # first let's see which vars are actually asked for
        # for now assume all keys means restriction on dims
        if not isinstance(merge, (list, tuple)):
            raise RuntimeError(
                "merge keyword must be a list of dimensions to merge together"
            )

        if len(merge) > 0 and not isinstance(merge[0], (list, tuple)):
            merge = [
                merge,
            ]

        for axis_id in kargs:
            if axis_id not in ids:
                raise ValueError("Invalid axis '%s'" % axis_id)
            index = ids.index(axis_id)
            value = kargs[axis_id]
            if isinstance(value, basestring):
                value = [value]
            if not isinstance(value, (list, tuple, slice)):
                raise TypeError(
                    "Invalid subsetting type for axis '%s', axes can only be subsetted by string,list or slice"
                    % axis_id
                )
            if isinstance(value, slice):
                axes[index] = axes[index].subAxis(value.start, value.stop, value.step)
                sh[index] = len(axes[index])
            else:  # ok it's a list
                for v in value:
                    if v not in axes[index][:]:
                        raise ValueError(
                            "Unkwown value '%s' for axis '%s'" % (v, axis_id)
                        )
                axis = cdms2.createAxis(value, id=axes[index].id)
                axes[index] = axis
                sh[index] = len(axis)

        array = numpy.ma.ones(sh, dtype=numpy.float)
        # Now let's fill this array
        self.get_array_values_from_dict_recursive(array, [], [], [], axes)

        # Ok at this point we need to take care of merged axes
        # First let's create the merged axes
        axes_to_group = []
        for merger in merge:
            merged_axes = []
            for axid in merger:
                for ax in axes:
                    if ax.id == axid:
                        merged_axes.append(ax)
            axes_to_group.append(merged_axes)
        new_axes = [groupAxes(grp_axes) for grp_axes in axes_to_group]
        sh2 = list(sh)
        for merger in merge:
            for merger in merge:  # loop through all possible merging
                merged_indices = []
                for id in merger:
                    merged_indices.append(axes_ids.index(id))
                for indx in merged_indices:
                    sh2[indx] = 1
                smallest = min(merged_indices)
                for indx in merged_indices:
                    sh2[smallest] *= sh[indx]

        myorder = []
        for index in range(len(sh)):
            if index in myorder:
                continue
            for merger in merge:
                merger = [axes_ids.index(x) for x in merger]
                if index in merger and index not in myorder:
                    for indx in merger:
                        myorder.append(indx)
            if index not in myorder:  # ok did not find this one anywhere
                myorder.append(index)

        outData = numpy.transpose(array, myorder)
        outData = numpy.reshape(outData, sh2)

        yank = []
        for merger in merge:
            merger = [axes_ids.index(x) for x in merger]
            mn = min(merger)
            merger.remove(mn)
            yank += merger
        yank = sorted(yank, reverse=True)
        for yk in yank:
            extract = (slice(0, None),) * yk
            extract += (0,)
            outData = outData[extract]
        # Ok now let's apply the newaxes
        sub = 0
        outData = MV2.array(outData)
        merged_axis_done = []
        for index in range(len(array.shape)):
            foundInMerge = False
            for imerge, merger in enumerate(merge):
                merger = [axes_ids.index(x) for x in merger]
                if index in merger:
                    foundInMerge = True
                    if imerge not in merged_axis_done:
                        merged_axis_done.append(imerge)
                        setMergedAxis = imerge
                    else:
                        setMergedAxis = -1
            if not foundInMerge:
                outData.setAxis(index - sub, axes[index])
            else:
                if setMergedAxis == -1:
                    sub += 1
                else:
                    outData.setAxis(index - sub, new_axes[setMergedAxis])
        outData = MV2.masked_greater(outData, 9.98e20)
        outData.id = "pmp"
        if order is not None:
            myorder = "".join(["({})".format(nm) for nm in order])
            outData = outData(order=myorder)
        # Merge needs cleaning for extra dims crated
        if merge != []:
            for i in range(outData.ndim):
                outData = scrap(outData, axis=i)
        outData = MV2.masked_greater(outData, 9.9e19)
        cdms2.setAutoBounds(ab)
        return outData
