from __future__ import print_function

import json
import os

# Populate default arguments
ArgDefaults = {}

ArgDefaults["--parameters"] = {"aliases": ["-p"]}

ArgDefaults["--modpath"] = {
    "aliases": ["--mp"],
    "type": "str",
    "dest": "modpath",
    "help": "Explicit path to model data",
}

ArgDefaults["--modnames"] = {
    "aliases": ["--mns"],
    "type": "ast.literal_eval",
    "dest": "modnames",
    "default": "None",
    "help": "A list of names that can be used to loop through modpath",
}

ArgDefaults["--mip"] = {
    "aliases": ["--MIP"],
    "type": "ast.literal_eval",
    "dest": "mip",
    "default": "None",
    "help": "A WCRP MIP project such as CMIP3 and CMIP5",
}

ArgDefaults["--exp"] = {
    "aliases": ["--EXP"],
    "type": "ast.literal_eval",
    "dest": "exp",
    "default": "None",
    "help": "An experiment such as AMIP, historical or pi-contorl",
}

ArgDefaults["--start_day"] = {
    "aliases": ["--sd"],
    "type": "ast.literal_eval",
    "dest": "startday",
    "default": "None",
    "help": "The start day of, for example, data to extract from a time series",
}

ArgDefaults["--start_month"] = {
    "aliases": ["--sm"],
    "type": "ast.literal_eval",
    "dest": "startmonth",
    "default": "None",
    "help": "The start month of, for example, data to extract from a time series",
}

ArgDefaults["--start_year"] = {
    "aliases": ["--sy"],
    "type": "ast.literal_eval",
    "dest": "startyear",
    "default": "None",
    "help": "The start year of, for example, data to extract from a time series",
}

ArgDefaults["--end_day"] = {
    "aliases": ["--ed"],
    "type": "ast.literal_eval",
    "dest": "endday",
    "default": "None",
    "help": "The end day of, for example, data to extract from a time series",
}

ArgDefaults["--end_month"] = {
    "aliases": ["--em"],
    "type": "ast.literal_eval",
    "dest": "endmonth",
    "default": "None",
    "help": "The end month of, for example, data to extract from a time series",
}

ArgDefaults["--end_year"] = {
    "aliases": ["--ey"],
    "type": "ast.literal_eval",
    "dest": "endyear",
    "default": "None",
    "help": "The end year of, for example, data to extract from a time series",
}

ArgDefaults["--seasons"] = {
    "aliases": ["--seas"],
    "type": "ast.literal_eval",
    "dest": "sea",
    "default": "None",
    "help": 'A list of seasons, e.g., ["DJF","JJA"]',
}

ArgDefaults["--results_dir"] = {
    "aliases": ["--rd"],
    "type": "str",
    "default": "None",
    "help": "The name of the folder where all runs will be stored.",
}

ArgDefaults["--case_id"] = {
    "aliases": ["--cid"],
    "dest": "modnames",
    "default": "None",
    "help": "The name of the subdirectory (below results_dir where results from a paritcular code execution is stored ",
}

ArgDefaults["--reference_data_path"] = {
    "aliases": ["--rdp"],
    "type": "str",
    "help": "The path/filename of reference (obs) data.",
}

ArgDefaults["--test_data_path"] = {
    "aliases": ["--tp"],
    "help": "The path/filename to model output.",
}

ArgDefaults["--diags"] = {
    "aliases": ["-d"],
    "help": "Path to other user-defined parameter file.",
    "help": "Path to other user-defined parameter file.",
    "type": "str",
    "nargs": "+",
    "required": False,
    "dest": "other_parameters",
}

ArgDefaults["--num_workers"] = {
    "aliases": ["-n"],
    "help": "Number of workers, used when running with multiprocessing or in distributed mode.",
    "type": "int",
    "required": False,
}

ArgDefaults['--scheduler_addr"'] = {
    "aliases": ["--N/A"],
    "help": "Address of scheduler in the form of IP_ADDRESS:PORT. Used when running in distributed mode.",
    "type": "str",
    "required": False,
}

ArgDefaults["--variables"] = {
    "aliases": ["--vars"],
    "help": "A list of variables to be processed",
}

# Write arguments json
if os.path.exists("DefArgsCIA.json"):
    print("File existing, purging: DefArgsCIA.json")
    os.remove("DefArgsCIA.json")

fH = open("DefArgsCIA.json", "w")
json.dump(
    ArgDefaults, fH, ensure_ascii=True, sort_keys=True, indent=4, separators=(",", ":")
)
fH.close()
