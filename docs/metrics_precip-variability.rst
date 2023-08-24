.. _metrics_precip-variability:

*******************************************
Precipitation Variability Across Timescales
*******************************************

Overview
========
This set of metrics is designed to measure precipitation variabilty across multiple timescales, including subdaily.

Demo
====
* `PMP demo Jupyter notebook`_

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

Spectral averages
*****************

Users will set up a parameter file and run the precipitation variability driver on the command line.
To run the driver, use: ::

   variability_across_timescales_PS_driver.py -p parameter_file  

Results are reported on a 2x2 degree latitude/longitude world grid.

Options available to set in the parameter file include:

* **mip**: Name of MIP. Use "obs" for reference datasets.
* **exp**: Name of experiment. 
* **var**: Name of data set variable, e.g. "pr". 
* **frq**: Frequency of data set, either "day" or "3hr". 
* **modpath**: Path to directory containing input data files. 
* **mod**: Name of model file or wildcard "*" to use all files in directory. Symlinks may be used. 
* **results_dir**: Results directory path.
* **case_id**: Case id.
* **prd**: Start and end years for analysis as list, e.g. [start_year, end_year].
* **fac**: Factor to convert from data set units to mm/day. Set to 1 for no conversion.
* **nperseg**: Length of segment in power spectra.
* **noverlap**: Length of overlap between segments in power spectra.
* **ref**: Reference data path.
* **cmec**: Set to True to output CMEC formatted JSON.

Metric 
******

The precipitation variability metric can be generated after model and observational spectral averages are made.

A script called `calc_ratio.py`_ is provided in the precip_variability codebase. This script can be called with three arguments to generate the ratio.

* **ref**: path to obs results JSON
* **modpath**: directory containing model results JSONS (not CMEC formatted JSONs)
* **results_dir**: directory for calc_ratio.py results

The calc_ratio.py script must be called with python directly. For example, to run this script using files from a directory called "results": ::

   python pcmdi_metrics/pcmdi_metrics/precip_variability/scripts_pcmdi/calc_ratio.py \
   --ref results/precip_variability/GPCP-1-3/PS_pr.day_regrid.180x90_area.freq.mean_GPCP-1-3.json \
   --modpath results/precip_variability/GISS-E2-H/ \
   --results_dir results/precip_variability/ratio/

Reference
==========
Ahn, M.-S., P. J. Gleckler, J. Lee, A. G. Pendergrass, and C. Jakob, 2022: Benchmarking Simulated Precipitation Variability Amplitude across Timescales. Journal of Climate. https://doi.org/10.1175/JCLI-D-21-0542.1


.. _PMP demo Jupyter notebook: https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/Demo_7_precip_variability.ipynb
.. _this link: https://github.com/PCMDI/pcmdi_metrics/tree/main/pcmdi_metrics/precip_variability/param
.. _calc_ratio.py: https://github.com/PCMDI/pcmdi_metrics/blob/main/pcmdi_metrics/precip_variability/scripts_pcmdi/calc_ratio.py
