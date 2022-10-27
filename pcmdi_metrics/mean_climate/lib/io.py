import json
import os

import pcmdi_metrics


class OBS(pcmdi_metrics.io.base.Base):
    def __init__(
        self, root, var, obs_dic, reference="default", file_mask_template=None
    ):

        template = (
            "%(realm)/%(frequency)/%(variable)/" + "%(reference)/%(ac)/%(filename)"
        )
        pcmdi_metrics.io.base.Base.__init__(self, root, template, file_mask_template)
        obs_name = obs_dic[var][reference]
        # usually send "default", "alternate", etc
        # but some case (sftlf) we send the actual name
        if isinstance(obs_name, dict):
            obs_name = reference
        ref = obs_dic[var][obs_name]
        obs_table = ref["CMIP_CMOR_TABLE"]

        if obs_table == "Omon":
            self.realm = "ocn"
            self.frequency = "mo"
            self.ac = "ac"
        elif obs_table == "fx":
            self.realm = ""
            self.frequency = "fx"
            self.ac = ""
        else:
            self.realm = "atm"
            self.frequency = "mo"
            self.ac = "ac"
        self.filename = ref["filename"]
        self.reference = obs_name
        self.variable = var


class JSONs(pcmdi_metrics.io.base.JSONs):
    def __init__(self, files=[], ignored_keys=None):
        if ignored_keys is None:
            ignored_keys = ["SimulationDescription"]
        super(JSONs, self).__init__(
            files,
            structure=[
                "variable",
                "model",
                "reference",
                "rip",
                "region",
                "statistic",
                "season",
            ],
            ignored_keys=ignored_keys,
        )

    def addJson(self, filename):
        f = open(filename)
        tmp_dict = json.load(f)
        json_struct = tmp_dict.get("json_structure", list(self.json_struct))
        json_version = tmp_dict.get("json_version", None)
        if json_version is None:
            # Json format not stored, trying to guess
            R = tmp_dict["RESULTS"]
            K = list(R.keys())
            for ky in K:
                try:
                    out = R[ky]  # get first available model
                    out = out["defaultReference"]  # get first set of obs
                    k = list(out.keys())
                    # print filename,"K IS:",k
                    k.pop(k.index("source"))
                    out = out[k[0]]  # first realization
                except Exception:
                    continue
                # Ok at this point we need to see if it is json std 1 or 2
                # version 1 had NHEX in every region
                # version 2 does not
                if "bias_xy_djf_NHEX" in list(out[list(out.keys())[0]].keys()):
                    json_version = "1.0"
                    json_struct = self.json_struct[1:]
                else:
                    json_version = "2.0"
                break
        if float(json_version) == 2.0:
            json_struct = json_struct[1:]
        # Now update our stored results
        # First we need to figure out the variable read in
        if "variable" not in json_struct:
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
        self.addDict2Self(tmp_dict, json_struct, json_version)
