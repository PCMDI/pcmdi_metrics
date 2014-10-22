PCMDI metrics package [![DOI](https://zenodo.org/badge/6619/UV-CDAT/uvcdat.png)](http://dx.doi.org/10.5281/zenodo.12251)
======

The PCMDI metrics package has been developed using functionality available from the UV-CDAT package to enabling research centers around the world to routinely benchmark their modeling systems
against a comprehensive suite of climate metrics. The package will enable modeling groups to compare their development model version(s) against all previous CMIP models. Currently, the package
is focused on well-established large- to global-scale climatological performance metrics that have been identified by the WGNE/WGCM metrics panel as useful for routine model benchmarking.


Package organization:

The package consists of four parts: 1) Analysis software, 2) an observationally-based database of global (or near global) annual cycle climatologies, 3) a database of performance metrics
computed for CMIP models and 4) documentation.


Getting started with the PCMDI metrics package:

The package has been developed to enable..



--- OLD STUFF ---

mean_climate_metrics_driver.py
------------------------------
USER executes to this to loop through variables and model results to calculate and output mean climate metrics.  Note: only one of the two files below (input_model_data.py, input_cmip5_model_data.py) should be imported (as discussed below). 

input_parameters.py
-------------------
USER sets variable list, obs path, metrics output path, and model clim interpolation option and data output path

input_cmip5_model_data.py
-------------------------
This file is imported in mean_climate_metrics_driver.py only when PCMDI is computing the CMIP5 metrics results.  There is no need for users at modeling centers to use this.  

input_model_data.py
-------------------
USER sets location and structure in in-house data, pointing to various to the versions of their model to be tested

mean_climate_metrics_calculations.py
------------------------------------
Mean climate metrics calculations

misc.py functions:
-------
get_target_grid
mkdir_fcn
get_our_model_clim
get_cmip5_model_clim
get_obs - obs_dictionary for different 'ref datasets
output_model_clims

portrait_plot subdirectory: 
--------------------------
WORK IN PROGRESS

input_cmip5_model_data.py
-------------------------
This file is imported in mean_climate_metrics_driver.py only when PCMDI is computing the CMIP5 metrics results.  There is no need for users at modeling centers to use this file.  It is included simply to demonstrate that the CMIP5 metrics computed at PCMDI (and provided as JSON files) have been computed with the identical code (mean_climate_metrics_calculations.py).	
