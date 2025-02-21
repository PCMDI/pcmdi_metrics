import os

# Define the path to the parameter file
#param_file_path = "debug_param_real.py"
param_file_path = "cmip_param_cmip5.py"
#param_file_path = "cmip_param_cmip6.py"
python_script = "real_monsoon_wang_driver.py"

# Define the range of values for nth (e.g., from 0 to 3)
nth_values = range(55)  # 0, 1, 2, 3

# Loop through each value of nth
for nth in nth_values:
    # Read the parameter file
    with open(param_file_path, "r") as file:
        lines = file.readlines()
    
    # Update the nth parameter in the file
    for i, line in enumerate(lines):
        if "nth" in line:  # Find the line that contains the nth parameter
            # Update the nth value
            lines[i] = f"nth = {nth}\n"
            break
    
    # Write the modified lines back to the parameter file
    with open(param_file_path, "w") as file:
        file.writelines(lines)
    
    # Run the python command with the updated parameter file
    os.system(f"python {python_script} -p {param_file_path}")
    print(f"Finished running with nth = {nth}")



# python monsoon_wang_driver.py -p cmip_param_cmip6.py --nth 7
