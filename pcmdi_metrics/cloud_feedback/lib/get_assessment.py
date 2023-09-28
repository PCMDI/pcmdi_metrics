#!/usr/bin/env python
# coding: utf-8

#=============================================
# calculate assessed and unassessed feedbacks
# revised from Zelinka et al (2022)
# by Li-Wei Chao (2022/02/25)
#=============================================

import numpy as np

# 10 hPa/dy wide bins:
width = 10
binedges=np.arange(-100,100,width)
x1=np.arange(binedges[0]-width,binedges[-1]+2*width,width)
binmids = x1+width/2.
cutoff = int(len(binmids)/2) 

def get_assessed_fbks(fbk_dict,obsc_fbk_dict):

    # dictionary is structured: [region][sfc][sec][name]

    assessed=[]
    fbk_names=[]
    
    # 1) Global high cloud altitude
    #===========================================
    LW = fbk_dict['eq90']['all']['HI680']['LWcld_alt']
    SW = fbk_dict['eq90']['all']['HI680']['SWcld_alt']
    assessed.append(LW+SW)
    fbk_names.append('High-Cloud Altitude')

    # 2) Tropical Ocean Descent Low AMT + TAU
    #===========================================
    # Unobscured components only:
    LW = obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['LWcld_amt'] + obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['LWcld_tau']
    SW = obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['SWcld_amt'] + obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['SWcld_tau']
    assessed.append(LW+SW)
    fbk_names.append('Tropical Marine Low-Cloud')

    # 3) Anvil
    #===========================================
    # Tropical oceanic ascent: High amt + high tau + delta obscuration-induced low
    LW = fbk_dict['eq30']['ocn_asc']['HI680']['LWcld_amt'] + fbk_dict['eq30']['ocn_asc']['HI680']['LWcld_tau'] +  \
          obsc_fbk_dict['eq30']['ocn_asc']['LO680']['LWdobsc_fbk']
    SW = fbk_dict['eq30']['ocn_asc']['HI680']['SWcld_amt'] + fbk_dict['eq30']['ocn_asc']['HI680']['SWcld_tau'] +  \
          obsc_fbk_dict['eq30']['ocn_asc']['LO680']['SWdobsc_fbk']
    assessed.append(LW+SW)
    fbk_names.append('Tropical Anvil Cloud')

    # 4) Global land cloud amount
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # CHANGE
    #===========================================
    # unobscured low cloud amount + high cloud amount + ∆obscuration
    LW = fbk_dict['eq90']['lnd']['HI680']['LWcld_amt'] + obsc_fbk_dict['eq90']['lnd']['LO680']['LWcld_amt'] +  \
                                                         obsc_fbk_dict['eq90']['lnd']['LO680']['LWdobsc_fbk']
    SW = fbk_dict['eq90']['lnd']['HI680']['SWcld_amt'] + obsc_fbk_dict['eq90']['lnd']['LO680']['SWcld_amt'] +  \
                                                         obsc_fbk_dict['eq90']['lnd']['LO680']['SWdobsc_fbk']
    assessed.append(LW+SW)
    fbk_names.append('Land Cloud Amount')

    # 5) Middle latitude cloud amount feedback
    #===========================================
    # Using the unobscured components:
    LW = obsc_fbk_dict['eq60']['ocn']['LO680']['LWcld_amt'] - obsc_fbk_dict['eq30']['ocn']['LO680']['LWcld_amt']
    SW = obsc_fbk_dict['eq60']['ocn']['LO680']['SWcld_amt'] - obsc_fbk_dict['eq30']['ocn']['LO680']['SWcld_amt']
    assessed.append(LW+SW)
    fbk_names.append('Middle Latitude Marine Low-Cloud Amount')

    # 6) Extratropical cloud optical depth feedback
    #===========================================
    # Using the unobscured components:
    LW = obsc_fbk_dict['eq70']['all']['LO680']['LWcld_tau'] - obsc_fbk_dict['eq40']['all']['LO680']['LWcld_tau']
    SW = obsc_fbk_dict['eq70']['all']['LO680']['SWcld_tau'] - obsc_fbk_dict['eq40']['all']['LO680']['SWcld_tau']
    assessed.append(LW+SW)
    fbk_names.append('High Latitude Low-Cloud Optical Depth')

    # 7) true_total
    #===========================================
    LW = fbk_dict['eq90']['all']['ALL']['LWcld_tot']
    SW = fbk_dict['eq90']['all']['ALL']['SWcld_tot']
    true_total = LW+SW

    sum_assessed = np.array(assessed).sum()
    imply_not_assessed = true_total - sum_assessed 
    assessed.append(imply_not_assessed)
    assessed.append(sum_assessed)
    assessed.append(true_total)
    
    fbk_names.append('Implied Unassessed Cloud Feedbacks')
    fbk_names.append('Sum of Assessed Cloud Feedbacks')
    fbk_names.append('Total Cloud Feedback')
    
    return(np.array(assessed),fbk_names) # size [fbk_types]  



def get_unassessed_fbks(fbk_dict,obsc_fbk_dict):

    # dictionary is structured: [region][sfc][sec][name]

    fbk_names=[]
    unassessed=[]
        
    # 1) Global unobscured low altitude (Complement to global high cloud altitude)
    #===========================================
    LW = obsc_fbk_dict['eq90']['all']['LO680']['LWcld_alt']
    SW = obsc_fbk_dict['eq90']['all']['LO680']['SWcld_alt']
    unassessed.append(LW+SW)
    fbk_names.append('Low-Cloud Altitude')

    # 2) Tropical Ocean Descent High AMT+TAU (Complement to Tropical Ocean Descent Low AMT+TAU)
    #===========================================
    # High AMT+TAU + ∆obscuration
    LW = fbk_dict['eq30']['ocn_dsc']['HI680']['LWcld_amt'] + fbk_dict['eq30']['ocn_dsc']['HI680']['LWcld_tau'] + \
                                                        obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['LWdobsc_fbk']
    SW = fbk_dict['eq30']['ocn_dsc']['HI680']['SWcld_amt'] + fbk_dict['eq30']['ocn_dsc']['HI680']['SWcld_tau'] + \
                                                        obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['SWdobsc_fbk']
    unassessed.append(LW+SW)
    fbk_names.append('Tropical Marine Subsidence\nHigh-Cloud Amount + Optical Depth')
    
    # 3) Complement to the Anvil
    #===========================================
    # Tropical oceanic ascent: unobscured low amt + low tau (complement to High amt + high tau + delta obscuration-induced low)
    LW = obsc_fbk_dict['eq30']['ocn_asc']['LO680']['LWcld_amt'] + obsc_fbk_dict['eq30']['ocn_asc']['LO680']['LWcld_tau']
    SW = obsc_fbk_dict['eq30']['ocn_asc']['LO680']['SWcld_amt'] + obsc_fbk_dict['eq30']['ocn_asc']['LO680']['SWcld_tau']
    unassessed.append(LW+SW)
    fbk_names.append('Tropical Marine Ascent\nLow-Cloud Amount + Optical Depth')
    
    # 4) Tropical land high+low optical depth (Complement to Global land cloud amount)
    #===========================================
    LW = fbk_dict['eq30']['lnd']['HI680']['LWcld_tau'] + obsc_fbk_dict['eq30']['lnd']['LO680']['LWcld_tau']
    SW = fbk_dict['eq30']['lnd']['HI680']['SWcld_tau'] + obsc_fbk_dict['eq30']['lnd']['LO680']['SWcld_tau']
    unassessed.append(LW+SW)
    fbk_names.append('Tropical Land Cloud Optical Depth')

    # 5) Complement to middle latitude cloud amount feedback
    #===========================================
    # 60-90 Ocean unobscured Low AMT
    #===========================================
    LW = obsc_fbk_dict['eq90']['ocn']['LO680']['LWcld_amt'] - obsc_fbk_dict['eq60']['ocn']['LO680']['LWcld_amt']
    SW = obsc_fbk_dict['eq90']['ocn']['LO680']['SWcld_amt'] - obsc_fbk_dict['eq60']['ocn']['LO680']['SWcld_amt']
    unassessed.append(LW+SW)
    fbk_names.append('60-90 Marine Low-Cloud Amount')

    # 6) Complement to Extratropical cloud optical depth feedback
    #===========================================
    # 30-40/70-90 Ocean+Land unobscured Low TAU
    #===========================================
    LW = obsc_fbk_dict['eq40']['all']['LO680']['LWcld_tau'] - obsc_fbk_dict['eq30']['all']['LO680']['LWcld_tau'] + \
         obsc_fbk_dict['eq90']['all']['LO680']['LWcld_tau'] - obsc_fbk_dict['eq70']['all']['LO680']['LWcld_tau']
    SW = obsc_fbk_dict['eq40']['all']['LO680']['SWcld_tau'] - obsc_fbk_dict['eq30']['all']['LO680']['SWcld_tau'] + \
         obsc_fbk_dict['eq90']['all']['LO680']['SWcld_tau'] - obsc_fbk_dict['eq70']['all']['LO680']['SWcld_tau']
    unassessed.append(LW+SW)
    fbk_names.append('30-40 / 70-90 Low-Cloud Optical Depth')
   
    # 7) 30-90 Ocean+Land High TAU
    #===========================================
    LW = fbk_dict['eq90']['all']['HI680']['LWcld_tau'] - fbk_dict['eq30']['all']['HI680']['LWcld_tau']
    SW = fbk_dict['eq90']['all']['HI680']['SWcld_tau'] - fbk_dict['eq30']['all']['HI680']['SWcld_tau']
    unassessed.append(LW+SW)
    fbk_names.append('30-90 High-Cloud Optical Depth')
   
    # 8) 30-90 Ocean High AMT + ∆obscuration
    #===========================================
    LW = fbk_dict['eq90']['ocn']['HI680']['LWcld_amt'] - fbk_dict['eq30']['ocn']['HI680']['LWcld_amt'] + \
    obsc_fbk_dict['eq90']['ocn']['LO680']['LWdobsc_fbk']  - obsc_fbk_dict['eq30']['ocn']['LO680']['LWdobsc_fbk']
    SW = fbk_dict['eq90']['ocn']['HI680']['SWcld_amt'] - fbk_dict['eq30']['ocn']['HI680']['SWcld_amt'] + \
    obsc_fbk_dict['eq90']['ocn']['LO680']['SWdobsc_fbk']  - obsc_fbk_dict['eq30']['ocn']['LO680']['SWdobsc_fbk']
    unassessed.append(LW+SW)
    fbk_names.append('30-90 Marine High-Cloud Amount')
        
    # 9) Obscuration covariance term
    #===========================================
    LW = obsc_fbk_dict['eq90']['all']['LO680']['LWdobsc_cov_fbk']
    SW = obsc_fbk_dict['eq90']['all']['LO680']['SWdobsc_cov_fbk']
    unassessed.append(LW+SW)
    fbk_names.append('Obscuration Covariance')

    # 10) Global Residual
    #===========================================
    LW = obsc_fbk_dict['eq90']['all']['LO680']['LWcld_err'] + fbk_dict['eq90']['all']['HI680']['LWcld_err']
    SW = obsc_fbk_dict['eq90']['all']['LO680']['SWcld_err'] + fbk_dict['eq90']['all']['HI680']['SWcld_err']
    unassessed.append(LW+SW)
    fbk_names.append('Zelinka Decomposition Residual')
    
    # 11) ocean ascent/descent Residual
    #===========================================
    LW_A = obsc_fbk_dict['eq30']['ocn']['LO680']['LWcld_amt'] + obsc_fbk_dict['eq30']['ocn']['LO680']['LWcld_tau'] +\
    fbk_dict['eq30']['ocn']['HI680']['LWcld_amt'] + fbk_dict['eq30']['ocn']['HI680']['LWcld_tau'] +\
    obsc_fbk_dict['eq30']['ocn']['LO680']['LWdobsc_fbk']
    SW_A = obsc_fbk_dict['eq30']['ocn']['LO680']['SWcld_amt'] + obsc_fbk_dict['eq30']['ocn']['LO680']['SWcld_tau'] +\
    fbk_dict['eq30']['ocn']['HI680']['SWcld_amt'] + fbk_dict['eq30']['ocn']['HI680']['SWcld_tau'] +\
    obsc_fbk_dict['eq30']['ocn']['LO680']['SWdobsc_fbk']
    
    LW_B = obsc_fbk_dict['eq30']['ocn_asc']['LO680']['LWcld_amt'] + obsc_fbk_dict['eq30']['ocn_asc']['LO680']['LWcld_tau'] +\
    fbk_dict['eq30']['ocn_asc']['HI680']['LWcld_amt'] + fbk_dict['eq30']['ocn_asc']['HI680']['LWcld_tau'] +\
    obsc_fbk_dict['eq30']['ocn_asc']['LO680']['LWdobsc_fbk'] +\
    obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['LWcld_amt'] + obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['LWcld_tau'] +\
    fbk_dict['eq30']['ocn_dsc']['HI680']['LWcld_amt'] + fbk_dict['eq30']['ocn_dsc']['HI680']['LWcld_tau'] +\
    obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['LWdobsc_fbk']
    SW_B = obsc_fbk_dict['eq30']['ocn_asc']['LO680']['SWcld_amt'] + obsc_fbk_dict['eq30']['ocn_asc']['LO680']['SWcld_tau'] +\
    fbk_dict['eq30']['ocn_asc']['HI680']['SWcld_amt'] + fbk_dict['eq30']['ocn_asc']['HI680']['SWcld_tau'] +\
    obsc_fbk_dict['eq30']['ocn_asc']['LO680']['SWdobsc_fbk'] +\
    obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['SWcld_amt'] + obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['SWcld_tau'] +\
    fbk_dict['eq30']['ocn_dsc']['HI680']['SWcld_amt'] + fbk_dict['eq30']['ocn_dsc']['HI680']['SWcld_tau'] +\
    obsc_fbk_dict['eq30']['ocn_dsc']['LO680']['SWdobsc_fbk']
    unassessed.append(LW_A+SW_A-LW_B-SW_B)
    fbk_names.append('Bony Omega Space Residual')
    
    sum_unassessed = np.array(unassessed).sum()
    unassessed.append(sum_unassessed)
    fbk_names.append('Sum of Unassessed Cloud Feedbacks')
    
    return(np.array(unassessed),fbk_names) # size [fbk_types]

