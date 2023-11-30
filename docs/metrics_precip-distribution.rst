.. _metrics_precip-distribution:

**************************
Precipitation Distribution
**************************

Overview
========
With the global domain partitioned into 62 regions, including 46 land and 16 ocean regions, we apply 10 established precipitation distribution metrics. The collection includes metrics focused on the maximum peak, lower 10th percentile, and upper 90th percentile in precipitation amount and frequency distributions; the similarity between observed and modeled frequency distributions; an unevenness measure based on cumulative amount; average total intensity on all days with precipitation; and number of precipitating days each year. 

Demo
====
In preparation

Exampe parameter files
======================
A set of example parameter files for models and observations can be viewed at `this link`_.

Required data sets 
==================

This driver expects daily averaged precipitation.

Input files must use the following name convention: ::

   variable_frequency_model_experiment_ensemble_startdate-enddate.nc  

Because underscores are used to separate these elements, they may not be used anywhere else in the file name.

Start and end dates must use the YYYYMMDD format.  

For example, these are valid input file names: ::

   pr_day_bcc-csm1-1_historical_r1i1p1_19800101-19841231.nc  
   pr_3hr_IMERG-v06B-Final_PCMDI_2x2_20100401-20100430.nc  

If the time series for a single data set is spread across multiple files, those files must be located in a single directory.

Usage
=====
Users will set up a parameter file and run the precipitation variability driver on the command line.
To run the driver, use: ::

   precip_distribution_driver.py -p parameter_file  

This code should be run for a reference observation initially as some metrics (e.g., Perkins score) need a reference.

After completing calculation for a reference observation, this code can work for multiple datasets at once.

This benchmarking framework provides three tiers of area averaged outputs for i) large scale domain (Tropics and Extratropics with separated land and ocean) commonly used in the PMP , ii) large scale domain with clustered precipitation characteristics (Tropics and Extratropics with separated land and ocean, and separated heavy, moderate, and light precipitation regions), and iii) modified IPCC AR6 regions shown in the reference paper.

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

Reference
=========
Ahn, M.-S., P. A. Ullrich, P. J. Gleckler, J. Lee, A. C. Ordonez, and A. G. Pendergrass, 2023: Evaluating Precipitation Distributions at Regional Scales: A Benchmarking Framework and Application to CMIP5 and CMIP6. Geoscientific Model Development, 16, 3927–3951, https://doi.org/10.5194/gmd-16-3927-2023
