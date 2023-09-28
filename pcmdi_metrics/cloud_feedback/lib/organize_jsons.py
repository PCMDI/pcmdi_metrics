# Load in the dictionary containing feedbacks or error metrics
# Compute NET = LW+SW feedbacks
# Append this dictionary to the existing json containing feedbacks and error metrics

from datetime import date 
import urllib.request
import numpy as np
import json

meta = {
"date_modified" :   str(date.today()),
"author"        :   "Mark D. Zelinka <zelinka1@llnl.gov>",
}

# Location of the cloud feedback and error metric jsons:
urlpath = 'https://raw.githubusercontent.com/mzelinka/assessed-cloud-fbks/main/data/'

def organize_fbk_jsons(new_dict,new_obsc_dict,mo,ripf):

    # Load in the existing file containing pre-computed CMIP6 feedbacks    
    fname = 'cmip6_amip-p4K_cld_fbks.json'
    with urllib.request.urlopen(urlpath+fname) as url:
        old_dict = json.load(url)   

    old_dict[mo]={} 
    old_dict[mo][ripf]={}
    old_dict[mo][ripf] = new_dict
    old_dict['metadata'] = meta

    # Load in the existing file containing pre-computed CMIP6 obscuration-related feedbacks
    fname = 'cmip6_amip-p4K_cld_obsc_fbks.json'
    with urllib.request.urlopen(urlpath+fname) as url:
        old_obsc_dict = json.load(url)

    old_obsc_dict[mo]={} 
    old_obsc_dict[mo][ripf]={}
    old_obsc_dict[mo][ripf] = new_obsc_dict
    old_obsc_dict['metadata'] = meta
    
    return(old_dict,old_obsc_dict) # now updated to include info from input dictionary 


def organize_err_jsons(new_dict,mo,ripf):

    # Load in the existing file containing pre-computed CMIP6 error metrics
    fname = 'cmip6_amip_cld_errs.json'
    with urllib.request.urlopen(urlpath+fname) as url:
        old_dict = json.load(url)

    names = ['E_TCA','E_ctpt','E_LW','E_SW','E_NET']
    old_dict[mo]={} 
    old_dict[mo][ripf]={}
    for region in new_dict['ALL'].keys():
        old_dict[mo][ripf][region]={}
        for sfc in ['all','ocn','lnd','ocn_asc','ocn_dsc']:
            old_dict[mo][ripf][region][sfc]={}
            for sec in ['ALL','HI680','LO680']:
                old_dict[mo][ripf][region][sfc][sec]={}
                for name in names:
                    # place in a natural order (e.g., Tropical marine low cloud amount = region/sfc/sec/name)
                    try:
                        old_dict[mo][ripf][region][sfc][sec][name] = new_dict[sec][region][sfc][name] 
                    except:
                        old_dict[mo][ripf][region][sfc][sec][name] = np.nan
                # end name loop
            # end section loop:
        # end sfc type loop
    # end region loop   
    old_dict['metadata'] = meta

    return(old_dict) # now updated to include info from input dictionary 


def organize_ecs_jsons(new_ecs,mo,ripf):

    ##################################################################
    # READ IN GREGORY ECS VALUES DERIVED IN ZELINKA ET AL (2020) GRL #
    ##################################################################
    with urllib.request.urlopen('https://raw.githubusercontent.com/mzelinka/cmip56_forcing_feedback_ecs/master/cmip56_forcing_feedback_ecs.json') as url:
        old_dict = json.load(url) 

    if new_ecs!=None:
        old_dict['CMIP6'][mo][ripf]['ECS'] = new_ecs

    return(old_dict) # now updated to include info from input dictionary 
