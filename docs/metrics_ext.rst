*****************
Extremes
*****************

Summary
========

The PMP Extremes driver produces annual block extrema and return values for daily temperature and precipitation data. The annual block extrema results include the `ETCCDI indices <http://etccdi.pacificclimate.org/list_27_indices.shtml>`_ Rx1day and Rx5day for precipitation and TX :sub:`x` , TX :sub:`n` , TN :sub:`x` , and TN :sub:`n`  for temperature.

Demo
=====
* `PMP demo Jupyter notebook`_

.. _PMP demo Jupyter notebook: https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/Demo_8_extremes.ipynb



Inputs
========

The Extremes Driver works on daily gridded climate data. This package expects input NetCDF files to be cf-compliant and on regular latitude/longitude grids. X and Y dimensions must be named "lon" and "lat", and the time dimension must be named "time". The input variables must be called "tasmax", "tasmin", or "pr". Input files must contain lat, lon, and time bounds.

Reference data
####################
A reference (observation) input is not required, but it is necessary to create (optional) Taylor Diagrams. Reference data sets must follow the above rules for variable names and bounds.

Land/sea mask
###################
Block extrema and return values will only be generated over land areas, so a land/sea mask is required for all datasets. Land is defined as grid cells where the land area percentage is between 50 and 100. Areas south of 50S will be masked out.

If available, users should provide the land/sea mask that accompanies their datasets. The mask variable in the land/sea mask file must be called "sftlf". If land/sea masks are scaled from 0-1, they will be rescaled to 0-100 on-the-fly. If land/sea masks are not provided, there is an option to generate them on-the-fly using pcmdi_utils. See the parameters section for more information.

Covariate data and stationarity
################################
The extremes driver can produce nonstationary return values for model-only runs. To generate nonstationary return values, users must provide a covariate file path and name (see the parameters section for these settings). If no covariate file is provided, the Extremes Driver will generate stationary return values.

The covariate file must contain an annual time series of the covariate variable. Covariate data must be provided in a NetCDF file with time bounds included. The covariate time dimension must either 1) be exactly the same length in years as the input data, or 2) overlap in years with the input data time dimension. It is recommended that a log transformation be applied to nonlinear time series such as recent carbon dioxide values.

Regional Analysis
#####################
You can either use a region from a shapefile or provide coordinate pairs that define the region. Consult the parameters section for more information.


Run
=====

To run the extremes metrics, use the following command format in a PMP environment:  
```extremes_driver.py -p parameter_file --other_params```

Outputs
========
The outputs will be written to a single directory. This directory will be created by the driver if it does not already exist. Otherwise, the output directory should be empty before the driver starts. The name of the output directory is controlled by the `metrics_output_path` and `case_id` parameters. 

This script will produce metrics JSONs, NetCDF files, and figures (optional). There will be NetCDF files containing block max/min values for temperature and/or precipitation, along with return value and standard error files. A metadata file called "output.json" will be generated with more detailed information about the files in the output bundle. Return value statistics will be provided for stationary return values only.

All NetCDF files will contain data for 5 time periods: Annual ("ANN"), DJF, MAM, JJA, and SON. Data is masked to be over land only (50<=sftlf<=100). Antarctica is excluded.

If multiple realizations are provided for a single model, a single return value file will be produced for that model which makes use of all provided realizations in the return value computation.

Metrics
##########
Metrics are produced to describe the time mean extrema values, along with spatial statistics comparing the mean model field to mean observed field. Metrics are output for Annual, DJF, MAM, JJA, and SON seasons.
Model only: "mean", "std_xy"  
If reference dataset is available: "mean", "std_xy", "std-obs_xy", "pct_dif", "bias_xy", "cor_xy", "mae_xy", "rms_xy", "rmsc_xy"  


Parameters
===========

The PMP extremes metrics can be controlled via an input parameter file, the command line, or both.  With the command line only it is executed via: ::

   extremes_driver.py  -p basic_param.py

or as a combination of an input parameter file and the command line, e.g.: ::

   extremes_driver.py  -p basic_param.py --vars rlut pr 

The following parameters are **required to be set by the user** either in a parameter file or on the command line:  

* **vars**: List of variables. Allowed values are any of ['pr','tasmax','tasmin'].
* **model_list**: List of model names.
* **realization**: List of realizations.
* **test_data_path**: File path to directory containing model/test data.
* **filename_template**: File name template for test data, e.g., "CMIP5.historical.%(model_version).r1i1p1.day.%(variable).19810101-200512.AC.v2019022512.nc" where "model_version" and "variable" will be analyzed for each of the entries in test_data_set and vars.
* **metric_output_path**: Directory path for metrics output in JSON files, e.g., '~/demo_data/PMP_metrics/'. The %(case_id) variable can be used here. If exists, should be empty before run. 

Reference data is optional, but the following parameters must be set when it is used:

* **reference_data_set**: A short name describing the reference dataset, e.g. "GPCP-1-3".
* **reference_data_path**: The reference data set file path.

To generate nonstationary return values (test data set only), use the following parameters:

* **covariate_path**: File path of covariate timeseries NetCDF. Must contain time bounds.
* **covariate**: Name of covariate variable in file given by --covariate_path.

The output of the extremes summary statistics are saved in a JSON file. 


In addition to the minimum set of parameters noted above, the following **additional options can be controlled**:

* **djf_mode**: Toggle how season containing December, January, and February is defined. "DJF" or "JFD". Default "DJF".
* **annual_strict**: This only matters for Rx5day. If True, only use data from within a given year in the 5-day means. If False, the rolling mean will include the last 4 days of the prior year. Default False.
* **drop_incomplete_djf**: If True, don't include data from the first January/February and last December in the analysis. Default False.
* **sftlf_filename_template**: The template for the test land/sea mask file. May contain placeholders %(model), %(model_version), or %(realization).
* **sftlf_filename_template**: The template for the reference land/sea mask file.
* **generate_sftlf**: Estimate a land-sea mask. If used in conjuction with --sftlf_filename_template, the template takes precedence.
* **case_id**: Save JSON and netCDF files into a subdirectory so that results from multiple tests can be readily organized.
* **plots**: Set to True to save world maps and Taylor Diagrams
* **msyear**: Start year for test data set.
* **meyear**: End year for test data set.
* **osyear**: Start year for reference data set.
* **oeyear**: End year for reference data set.
* **regrid**: Set to False to skip regridding if all test and reference data sets are on the same grid.
* **ModUnitsAdjust**: Provide information for units conversion. Uses format (flag (bool), operation (str), value (float), new units (str)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 86400, 'mm/day') to convert kg/m2/s to mm/day.
* **ObsUnitsAdjust**: Similar to ModUnitsAdjust, but for reference dataset.

The following parameters are used for regional analysis using a shapefile:

* **shp_path**: Path to shapefile.
* **attribute**: Attribute used to identify region (eg, column of attribute table). For example, "COUNTRY" in a shapefile of countries.
* **region_name**: Unique feature value of the region that occurs in the attribute given by "--attribute". Must match only one geometry in the shapefile. An example is "NORTH_AMERICA" under the attribute "CONTINENTS".

These parameters are used for regional analysis using a coordinate list:

* **coords**: Coordinate lat/lon pair lists. The coordinate must be listed in consecutive order, as they would occur when walking the perimeter of the bounding shape. Does not need to be a box, but cannot have holes. For example [[lat1,lon1],[lat1,lon2],[lat2,lon2],[lat2,lon1]].
* **region_name**: Name of region. Default is "custom".

Extreme value analysis details
==============================

For this driver, we have implemented the Generalized Extreme Value analysis in pure Python. The return value results may vary from those obtained with the R climextRemes package, which was used to conduct the return value analysis in Wehner, Gleckler, and Lee (2000). In the nonstationary case, the GEV location parameter is linearly dependent on the covariate.

Reference
==========

Michael Wehner, Peter Gleckler, Jiwoo Lee, 2020: Characterization of long period return values of extreme daily temperature and precipitation in the CMIP6 models: Part 1, model evaluation, Weather and Climate Extremes, 30, 100283, https://doi.org/10.1016/j.wace.2020.100283.
