.. _metrics_precip-distribution:

**************************
Precipitation Distribution
**************************

Overview
========


Exampe parameter files
======================
A set of example parameter files for models and observations can be viewed at `this link`_.

Required data sets 
==================

Input files must use the following name convention: ::

   variable_frequency_model_experiment_ensemble_startdate-enddate.nc  

Because underscores are used to separate these elements, they may not be used anywhere else in the file name.

Start and end dates must use the YYYYMMDD or YYYYMMDDHHHH format.  

For example, these are valid input file names: ::

   pr_day_bcc-csm1-1_historical_r1i1p1_19800101-19841231.nc  
   pr_3hr_IMERG-v06B-Final_PCMDI_2x2_201004010000-201004302100.nc  

If the time series for a single data set is spread across multiple files, those files must be located in a single directory.

Usage
=====
Users will set up a parameter file and run the precipitation variability driver on the command line.
To run the driver, use: ::

   precip_distribution_driver.py -p parameter_file  

Options available to set in the parameter file include:

* **mip**: Name of MIP.
* **var**: Name of data set variable, e.g. "pr". 
* **frq**: Frequency of data set, either "day" or "3hr". 
* **modpath**: Path to directory containing input data files. 
* **mod**: Name of model file or wildcard "*" to use all files in directory. Symlinks may be used. 
* **results_dir**: Results directory path.
* **case_id**: Case id.
* **prd**: Start and end years for analysis as list, e.g. [start_year, end_year].
* **fac**: Factor to convert from data set units to mm/day. Set to 1 for no conversion.
* **res**: List of target horizontal resolutions in degrees for interporation.
* **ref**: Reference data path.
* **ref_dir**: Reference directory path.
* **cmec**: Set to True to output CMEC formatted JSON.


.. _this link: https://github.com/PCMDI/pcmdi_metrics/tree/main/pcmdi_metrics/precip_distribution/param
