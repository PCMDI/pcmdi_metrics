import json
import os
import matplotlib.pyplot as plt

#directory = 'CMIP_results/CMIP5/'

def read_stats(json_file, region_name, stats_name):

    with open(json_file, 'r') as f:
        data = json.load(f)
    
    cor_values = []
    
    for model, regions in data.items():
        for region, stats in regions.items():
            #if region == "EASM" and "rmsn" in stats:
            #    cor_values.append(float(stats["rmsn"]))
            if region == region_name and stats_name in stats:
                cor_values.append(float(stats[stats_name]))
    
    
    return cor_values


directory = 'CMIP_results/CMIP6/'
json_file = os.path.join(directory,'combined_results.json')

cmip6 = read_stats(json_file, 'EASM', 'rmsn')
#print(cmip6)

directory = 'CMIP_results/CMIP5/'
json_file = os.path.join(directory,'combined_results.json')

cmip5 = read_stats(json_file, 'EASM', 'rmsn')
print(cmip5)




plt.figure(figsize=(8, 6))

plt.scatter([0]*len(cmip5), cmip5, color='blue', label='CMIP5', s=100, zorder=3)
plt.scatter([1]*len(cmip6), cmip6, color='red', label='CMIP6', s=100, zorder=3)

plt.xticks([0, 1], ['CMIP5', 'CMIP6'])

plt.ylabel('Data values')
plt.xlabel('Model Categories')

plt.title('CMIP5 vs CMIP6 Data Comparison')
plt.show()
