# Load in the dictionary containing feedbacks or error metrics
# Compute NET = LW+SW feedbacks
# Append this dictionary to the existing json containing feedbacks and error metrics

import numpy as np
import json
from datetime import date 

datadir = '../data/'

meta = {
"date_modified" :   str(date.today()),
"author"        :   "Mark D. Zelinka <zelinka1@llnl.gov>",
}

def organize_fbk_jsons(new_dict,new_obsc_dict,mo,ripf):

    # Load in the existing file containing pre-computed CMIP6 feedbacks
    file = datadir+'cmip6_amip-p4K_cld_fbks.json'
    f = open(file,'r')
    old_dict = json.load(f)
    f.close()

    old_dict[mo]={} 
    old_dict[mo][ripf]={}
    old_dict[mo][ripf] = new_dict
    old_dict['metadata'] = meta

    # Load in the existing file containing pre-computed CMIP6 obscuration-related feedbacks
    file = datadir+'cmip6_amip-p4K_cld_obsc_fbks.json'
    f = open(file,'r')
    old_obsc_dict = json.load(f)
    f.close()

    old_obsc_dict[mo]={} 
    old_obsc_dict[mo][ripf]={}
    old_obsc_dict[mo][ripf] = new_obsc_dict
    old_obsc_dict['metadata'] = meta
    
    return(old_dict,old_obsc_dict) # now updated to include info from input dictionary 


def organize_err_jsons(new_dict,mo,ripf):

    # Load in the existing file containing pre-computed CMIP6 error metrics
    file = datadir+'cmip6_amip_cld_errs.json'
    f = open(file,'r')
    old_dict = json.load(f)
    f.close()

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
    f = open(datadir+'cmip56_forcing_feedback_ecs.json','r')
    old_dict = json.load(f)
    f.close()

    if new_ecs!=None:
        old_dict['CMIP6'][mo][ripf]['ECS'] = new_ecs

    return(old_dict) # now updated to include info from input dictionary 
