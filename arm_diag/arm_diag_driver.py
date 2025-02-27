#!/usr/bin/env python
import os,subprocess,sys

##User defined data and code pahs
#PMP code path
pmpcode_path="/global/cfs/cdirs/mp193/PMP_ARMDiag/pcmdi_metrics/"

#Paths for arm_driver and json file
arm_driver_path = pmpcode_path + "/pcmdi_metrics/arm_diag/arm-gcm-diagnostics/arm_diags/arm_driver.py"
user_arm_driver_json_path = pmpcode_path + "/pcmdi_metrics/arm_diag/arm-gcm-diagnostics/arm_diags/diags_all_multisites_for_cmip6.json"

default_arm_driver_json_name="diags_all_multisites_for_cmip6.json"

#Input data path and case name
#user defined paths (change the following accordingly)
user_case_id = "output_testperlmutter_armdiags_v4"

user_armdiags_path= pmpcode_path + "/pcmdi_metrics/arm_diag/arm-gcm-diagnostics/"
user_test_data_set = "testmodel"
user_data_base_path = "/global/cfs/cdirs/mp193/PMP_ARMDiag/ARM_DATA/arm_diags_data_v4.0_09242024/"

user_output_path = "/global/cfs/cdirs/mp193/PMP_ARMDiag/ARMDIAGOUTPUT/"

#default paths (don't modify)
default_case_id = "output_cheng_20240905_armdiags_v4"

default_armdiags_path="/Users/tao4/Documents/ARM_Infrastructure/ARM_DIAG/arm-gcm-diagnostics/"
default_test_data_set = "testmodel"
default_data_base_path = "/Users/tao4/Documents/ARM_Infrastructure/ARM_DIAG/arm_diags_data_v3.1_06122023/"

default_output_path = "/Users/tao4/Documents/ARM_Infrastructure/ARM_DIAG/"

basic_para_path = pmpcode_path + "/pcmdi_metrics/arm_diag/arm-gcm-diagnostics/arm_diags/basicparameter.py"

## Setup the proper paths for ARM_Diag based on user defined paths above
def replace_text_in_file(file_path, old_text, new_text):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = content.replace(old_text, new_text)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("Text replacement successful.")
    except Exception as e:
        print(f"Error: {e}")


#replace_text_in_file(file_path, old_text, new_text)
replace_text_in_file(arm_driver_path, default_arm_driver_json_name, user_arm_driver_json_path)

replace_text_in_file(basic_para_path, default_case_id, user_case_id)
replace_text_in_file(basic_para_path, default_armdiags_path, user_armdiags_path)
replace_text_in_file(basic_para_path, default_test_data_set, user_test_data_set)
replace_text_in_file(basic_para_path, default_data_base_path, user_data_base_path)
replace_text_in_file(basic_para_path, default_output_path, user_output_path)

##

print("Starting ARM Diagnostic Package Calculation!")

path1='arm-gcm-diagnostics/arm_diags/'
path2='arm-gcm-diagnostics/arm_diags/'

arm_diag_call = 'python '+ path1 + 'arm_driver.py -p ' +path2+ 'basicparameter.py'
print(arm_diag_call)
process1 = subprocess.Popen(arm_diag_call, shell=True)
process1.wait()

print("Done!")
