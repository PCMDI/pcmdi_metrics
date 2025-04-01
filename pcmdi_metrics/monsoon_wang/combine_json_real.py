import os
import json
import sys

def combine_results(directory):
    combined_results = {}

    # Loop through all .json files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            
            # Open and read the json file
            with open(file_path, 'r') as file:
                data = json.load(file)
                
                # Check if 'RESULTS' key exists in the json data
                if 'RESULTS' in data:
                    # Merge the 'RESULTS' section into the combined_results
                    for key, value in data['RESULTS'].items():
                        if key not in combined_results:
                            combined_results[key] = value
                        else:
                            # If the key exists, combine the sub-dictionaries (you can customize this behavior)
                            for sub_key, sub_value in value.items():
                                if sub_key not in combined_results[key]:
                                    combined_results[key][sub_key] = sub_value
                                else:
                                    # If sub_key exists, decide how to combine (e.g., add, average, etc.)
                                    combined_results[key][sub_key] = sub_value
    
    return combined_results


models = 'CMIP5'
region = 'AllM'

#directory = 'CMIP_results/CMIP5/'
#directory = 'CMIP_results/CMIP6/'


directory = os.path.join('CMIP_results',models, region)
print(directory)


combined_results = combine_results(directory)

#print(json.dumps(combined_results, indent=4))

#out_json_file = os.path.join(directory,'combined_results.json')
#out_json_file = 'combined_results_cmip5.json'
#out_json_file = 'combined_results_cmip6.json'
out_json_file = os.path.join('CMIP_results','combined_results_'+models+'_'+region+'.json')

#with open('combined_results.json', 'w') as outfile:
with open(out_json_file, 'w') as outfile:
    json.dump(combined_results, outfile, indent=4)

