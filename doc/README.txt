WGNE/WGCM metrics panel package - alpha v0.1

mean_climate_metrics_driver.py
------------------------------

USER executes to this to loop through variables and model results to calculate and output mean climate metrics.  Note: only one of the two files below (input_model_data.py, input_cmip5_model_data.py) should be imported (as discussed below). 

input_parameters.py
-------------------
USER sets variable list, obs path, metrics output path, and model clim interpolation option and data output path

input_cmip5_model_data.py
-------------------------
This file is imported in mean_climate_metrics_driver.py only when PCMDI is
computing the CMIP5 metrics results.  There is no need for users at modeling
centers to use this.  

input_model_data.py
-------------------
USER sets location and structure in in-house data, pointing to various to the versions of there model to be tested

mean_climate_metrics_calculations.py
------------------------------------
Mean climate metrics calculations

misc.py functions:
------
get_target_grid
mkdir_fcn
get_our_model_clim
get_cmip5_model_clim
get_obs - obs_dictionary for different 'ref datasets
output_model_clims

portriat_plot subdirectory: 
--------------------------
WORK IN PROGRESS


input_cmip5_model_data.py
-------------------------
This file is imported in mean_climate_metrics_driver.py only when PCMDI is
computing the CMIP5 metrics results.  There is no need for users at modeling
centers to use this file.  It is included simply to demonstrate that the CMIP5
metrics computed at PCMDI (and provided as JSON files) have been computed with
the identical code (mean_climate_metrics_calculations.py).

	
