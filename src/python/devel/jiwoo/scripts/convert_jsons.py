#!/usr/bin/env python
from __future__ import print_function
import json
import pcmdi_metrics
import collections

parser = pcmdi_metrics.driver.pmp_parser.PMPParser()

parser.add_argument("--input-file", "-i", help="input file")
args = parser.get_parameter()
with open(args.input_file) as f:
    d = json.load(f)

correct = collections.OrderedDict(d)
# first the obs in type does not belong, thre creating a description section
correct["obs"] = correct["RESULTS"].pop("obs")
correct["RESULTS"] = {}
correct["descriptions"] = {"models": {}, "metrics": {}}
models = d["RESULTS"]["model"]
stats_names = ["nonlinearity", "nonlinearity_error", "value", "value_error"]
for m in d["RESULTS"]["model"]:
    correct["descriptions"]["models"][m] = {"description_of_the_collection":
                                            models[m]["description_of_the_collection"]}
    correct["descriptions"]["models"][m]["name"] = models[m]["name"]
    correct["descriptions"]["metrics"][m] = {}
    # Ok now the "metrics" section can be moved up
    for metric in models[m]["metrics"]:
        #correct["descriptions"]["models"][metric][m] = {}
        if not metric in correct["RESULTS"]:
            correct["RESULTS"][metric] = {m: {"raw":{},"metric":{}}}
        else:
            correct["RESULTS"][metric][m] = {"raw":{},"metric":{}}
        # Ok now create the reference section
        metrics = models[m]["metrics"][metric]
        if metric in correct["descriptions"]["metrics"]:
            correct["descriptions"]["metrics"][metric][m] = {}
        else:
            correct["descriptions"]["metrics"][metric]={m:{}}
        for att in ["datasets", "method_to_compute_metric"]:
            correct["descriptions"]["metrics"][metric][m][att] = metrics[att]
        # Ok the real reorg now
        raw = metrics["raw_values"]
        raw_obs = raw["observations"]
        for key in raw_obs:
            sp = key.split("_")
            if len(sp) == 1:
                new_key = sp[0]
            else:
                new_key = sp[1]+"_"+sp[-1]
            correct["descriptions"]["metrics"][metric][m][new_key] = {}
            correct["RESULTS"][metric][m]["raw"][new_key] = {}
            for att in raw_obs[key]:
                if att in stats_names:
                    correct["RESULTS"][metric][m]["raw"][new_key][att] = raw_obs[key][att]
                else:
                    correct["descriptions"]["metrics"][metric][m][new_key][att] = raw_obs[key][att]
        raw_model = raw["model"]
        correct["RESULTS"][metric][m]["raw"]["model"] = {}
        for att in raw_model:
            if att in stats_names:
                correct["RESULTS"][metric][m]["raw"]["model"][att] = raw_model[att]
            else:
                correct["descriptions"]["metrics"][metric][m][att] = raw_model[att]
        # Now the actual results
        model_metrics = metrics["metric_values"]
        for key in model_metrics:
            sp = key.split("_")
            if len(sp) == 2:
                new_key = sp[1]
            else:
                new_key = sp[2]+"_"+sp[-1]
            correct["RESULTS"][metric][m]["metric"][new_key] = {}
            for att in stats_names:
                if att in model_metrics[key]:
                    correct["RESULTS"][metric][m]["metric"][new_key][att] = model_metrics[key][att]
# Now need to tell it the real struct
correct["json_structure"] = ["metric", "model", "type", "source", "statistic"]

new_name = args.input_file[:-5]+"_reformatted.json"
with open(new_name, "w") as f:
    json.dump(correct, f, indent=4)
print("Done, look at:", new_name)
