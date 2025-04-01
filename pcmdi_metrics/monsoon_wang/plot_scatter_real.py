import json
import os
import matplotlib.pyplot as plt
import sys
import numpy as np

#directory = 'CMIP_results/CMIP5/'

def read_stats_old(json_file, region_name, stats_name):

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



def read_stats(json_file, region_name, stats_name):

    with open(json_file, 'r') as f:
        data = json.load(f)
    
    rmsn_values = []
    model_keys = []
    
    for model, realizations in data.items():
    
        model_rmsn = []
        
        for realization, regions in realizations.items():
    
            #if 'EASM' in regions and 'rmsn' in regions['EASM']:
            #    model_rmsn.append(float(regions['EASM']['rmsn']))
            if region_name in regions and stats_name in regions[region_name]:
                model_rmsn.append(float(regions[region_name][stats_name]))
        
        rmsn_values.append(model_rmsn)
        model_keys.append(model)

    return rmsn_values, model_keys



#models = 'CMIP5'

region = 'EASM'
region = 'SAMM'
region = 'NAMM'
region = 'NAFM'
region = 'SAFM'



stat = 'rmsn'
#stat = 'cor'
#stat = 'threat_score'

model_list = []

directory = 'CMIP_results/'
#directory = 'CMIP_results/CMIP6/'
#directory = os.path.join('CMIP_results',models, region)

#json_file = os.path.join(directory,'combined_results.json')
#json_file = os.path.join('CMIP_results','combined_results_'+models+'_'+region+'.json')
json_file = os.path.join('CMIP_results','combined_results_'+'CMIP5'+'_'+region+'.json')

cmip5, model_keys = read_stats(json_file, region, stat)
#print(len(cmip5))

model_list.extend(model_keys)

json_file = os.path.join('CMIP_results','combined_results_'+'CMIP6'+'_'+region+'.json')

cmip6, model_keys = read_stats(json_file, region, stat)
#print(cmip6)
#print(len(cmip6))

model_list.extend(model_keys)

cmip56 = cmip5 + cmip6
#print(cmip56)

#print(model_keys)
#print(model_list)
#print(len(cmip56))
#sys.exit()


medians = [np.median(row) for row in cmip56]

medians_cmip5 = [np.median(row) for row in cmip5]
medians_cmip6 = [np.median(row) for row in cmip6]

median_cmip5 = np.median(medians_cmip5)
median_cmip6 = np.median(medians_cmip6)

##################################################
fig, ax = plt.subplots(figsize=(10, 6))

#ax.bar(range(len(cmip56)), medians, align='center', color='skyblue', edgecolor='black')

x1 = np.arange(len(medians_cmip5))
x2 = np.arange(len(medians_cmip6)) + len(medians_cmip5)

bars1 = ax.bar(x1, medians_cmip5, width=0.7, label='CMIP5', color='skyblue')
bars2 = ax.bar(x2, medians_cmip6, width=0.7, label='CMIP6', color='lightgreen')

for i, (row, model_key) in enumerate(zip(cmip56, model_list)):
    #print("i = ", i, '  row = ', row, ' model = ', model_key)
    #print("[i] * len(row) = ", [i] * len(row))
    ax.scatter([i] * len(row), row, color='LightCoral', zorder=2, s=3)


ax.axhline(median_cmip5, color='skyblue', linestyle='--', label=f'Median CMIP5: {median_cmip5:.2f}')
ax.axhline(median_cmip6, color='lightgreen', linestyle='--', label=f'Median CMIP6: {median_cmip6:.2f}')


ax.set_xticks(range(len(cmip56)))
#ax.set_xticklabels(model_list)
ax.set_xticklabels(model_list, rotation=45, ha='right', fontsize=5)
#ax.set_ylabel('RMSN', fontsize=15)
#ax.set_title('Realization Median of RMSN of Monsoon Precipitation Intensity, '+region+', ref=GPCP', fontsize=12)
#ax.set_ylabel('PCC', fontsize=15)
#ax.set_title('Realization Median of Pattern Correlation of Monsoon Precipitation Intensity, '+region+', ref=GPCP', fontsize=12)

#ax.set_ylabel('Threat Score', fontsize=15)
#ax.set_title('Realization Median of Threat Score of Monsoon Precipitation Intensity, '+region+', ref=GPCP', fontsize=12)

ax.set_ylabel(f'{stat}', fontsize=15)
ax.set_title(f'Realization Median of {stat} of Monsoon Precipitation Intensity, '+region+', ref=GPCP', fontsize=12)

ax.legend(labelspacing=0.2, borderpad=0.3, markerscale=0.5, fontsize=10, frameon=False)

plt.tight_layout()
plt.show()



