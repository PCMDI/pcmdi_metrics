import datetime
import json
import os
import sys

config_json = sys.argv[1]
out_file_name = sys.argv[2]
pmp_config = sys.argv[3]

try:
    with open(config_json) as config:
        settings = json.load(config)["PMP/"+pmp_config]
except json.decoder.JSONDecodeError:
    print("Error: could not read " + config_json + ". File might not be valid JSON.")
    sys.exit(1)

param_file = open(out_file_name, "w")

param_file.write("import os\n")
param_file.write("import datetime\n")
param_file.write("\n")

for item in settings:
    val = settings[item]
    # JSON doesn't support several data types, including tuples,
    # dictionaries, and functions. We use the eval statement
    # to extract those from strings in the config file.
    if isinstance(val,str):
        # get tuples
        if (val[0] == '(') and (val[-1] == ')'):
            val = eval(val)
        # get dictionary
        elif (val[0] == '{') and (val[-1] == '}'):
            val = eval(val)
        # get functions
        elif (val[-1] == ')'):
            val = eval(val)
        # also possible someone wrote a bool as a string:
        elif ((val == 'true') or (val == 'True')):
            val = True
        elif ((val == 'false') or (val == 'False')):
            val = False

    # write parameters to file
    if isinstance(val,str):
        # Need to add quotes for string
        param_file.write("{0} = \'{1}\'\n".format(item,val))
    else:
        param_file.write("{0} = {1}\n".format(item,val))

param_file.close()