#!/usr/bin/env python
import json
import os


class MetadataFile:
    # This class organizes the contents for the CMEC
    # metadata file called output.json, which describes
    # the other files in the output bundle.

    def __init__(self, metrics_output_path):
        self.outfile = os.path.join(metrics_output_path, "output.json")
        self.json = {
            "provenance": {
                "environment": "",
                "modeldata": "",
                "obsdata": "",
                "log": "",
            },
            "metrics": {},
            "data": {},
            "plots": {},
        }

    def update_metrics(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["metrics"].update({kw: tmp})
        return

    def update_data(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["data"].update({kw: tmp})
        return

    def update_plots(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["plots"].update({kw: tmp})

    def update_provenance(self, kw, data):
        self.json["provenance"].update({kw: data})
        return

    def update_index(self, val):
        self.json["index"] = val
        return

    def write(self):
        with open(self.outfile, "w") as f:
            json.dump(self.json, f, indent=4)
