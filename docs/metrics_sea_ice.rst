*****************
Sea Ice
*****************

Summary
========
The PCMDI Metrics Package (PMP) sea ice driver produces metrics that compare modeled and observed sea ice extent as shown in `Ivanova et al. (2016)`_. These metrics are generated for total sea ice extent in eight preset sectors. They can be compared across models, realizations, and regions.

Demo
=====
* `PMP demo Jupyter notebook`_

.. _PMP demo Jupyter notebook: https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/Demo_9_seaIceExtent_ivanova.ipynb

Inputs
======
The sea ice driver uses monthly mean sea ice concentration and grid area data to generate sea ice extent metrics. An unlimited number of test data sets (typically model data) may be provided if file names follow a common template. A single reference data set is required, which is typically a observational data set or a model control run. For best results, all data files should contain latitude and longitude variables that are named "latitude" and "longitude" or "lat" and "lon". Data may use an irregular grid if latitude and longitude variables are included, preferably as additional coordinates. If multiple realizations of a model are provided, all realizations must use the same grid. See the Parameters section for more details about inputs.

Run
====
The PMP sea ice metrics can be controlled via an input parameter file, the command line, or both. With the command line only it is executed via: ::

    sea_ice_driver.py -p parameter_file.py

or as a combination of an input parameter file and the command line, e.g.: ::

    sea_ice_driver.py -p parameter_file.py --msyear 1991 --meyear 2020

Outputs
=======
The driver produces two JSON files. The first contains mean square error metrics for all input models and realizations relative to the reference data set. The second contains sea ice climatology and area data. The driver also produces a bar chart displaying these metrics.

Sectors
########
The metrics results are provided for eight different geographic regions. In the Northern Hemisphere there are the Arctic, North Pacific, North Atlantic, and Central Arctic regions. In the Southern Hemisphere there are the Antarctic, South Pacific, South Atlantic, and Indian Ocean regions. The region definitions can be found in `Ivanova et al. (2016)`_.

.. _Ivanova et al. (2016): https://doi.org/10.1175/JCLI-D-16-0026.1

Parameters
==========
A `demo parameter file`_ is provided in the sea ice code.  

.. _demo parameter file: https://github.com/PCMDI/pcmdi_metrics/blob/405_sic_ao/pcmdi_metrics/sea_ice/param/parameter_file.py
  
* **case_id**: Save JSON and figure files into this subdirectory so that results from multiple tests can be readily organized.
* **test_data_set**: List of model names.
* **realization**: List of realizations or "*" to use all realizations.
* **test_data_path**: File path to directory containing model/test data.
* **filename_template**: File name template for test data, e.g., "%(variable)_SImon_%(model_version)_historical_r1i2p2f1_gr_201001-201112.nc" where "model_version" and "variable" will be analyzed for each of the entries in test_data_set and vars.
* **var**: Name of model sea ice variable
* **msyear**: Start year for test data set.
* **meyear**: End year for test data set.
* **ModUnitsAdjust**: Factor to convert model sea ice data to fraction of 1. Uses format (flag (bool), operation (str), value (float)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 1e-2) to convert from percent concentration to decimal concentration.
* **area_template**: File path of model grid area data.
* **area_var**: Name of model area variable, e.g. "areacello"
* **AreaUnitsAdjust**: Factor to convert model area data to units of km :sup:`2` . Uses format (flag (bool), operation (str), value (float)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 1e-6) to convert from m :sup:`2`  to km :sup:`2` .
* **metrics_output_path**: Directory path for metrics output in JSON files, e.g., '~/demo_data/PMP_metrics/'. The %(case_id) variable can be used here. If exists, should be empty before run.
* **reference_data_path_nh**: The reference data file path for the northern hemisphere. If data is global, provide same path for nh and sh.
* **reference_data_path_sh**: The reference data file path for the southern hemisphere. If data is global, provide same path for nh and sh.
* **ObsUnitsAdjust**: Factor to convert reference sea ice data to fraction of 1. Uses format (flag (bool), operation (str), value (float)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 1e-2) to convert from percent concentration to decimal concentration.
* **reference_data_set**: A short name describing the reference dataset, e.g. "OSI-SAF".
* **osyear**: Start year for reference data set.
* **oeyear**: End year for reference data set.
* **obs_var**: Name of reference sea ice variable.
* **ObsAreaUnitsAdjust**: Factor to convert model area data to units of km :sup:`2` . Uses format (flag (bool), operation (str), value (float)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 1e-6) to convert from m :sup:`2`  to km :sup:`2` .
* **obs_area_template**: File path of grid area data. If unavailalbe, skip and use "obs_cell_area".
* **obs_area_var**: Name of reference area variable, if available. If unavailable, skip and use "obs_cell_area".
* **obs_cell_area**: For equal area grids, the area of a single grid cell in units of km :sup:`2` . Only required if obs area file is not available.
* **pole**: Set the maximum latitude for the Central Arctic and Arctic regions to exclude ice over the pole. Default is 90.1 to include all ice.

Postprocessing
==============

A script is provided to create a multi-model bar chart using results from multiple runs of the sea ice driver. This script can be found in ./scripts/sea_ice_figures.py. 

Example command: ::

    python sea_ice_figures.py --filelist 'path/to/models/*/sea_ice_metrics.json' --output_path '.'


A wildcard '*' can be used to glob multiple folders of results. The final path in the --filelist parameter must be the sea_ice_metrics.json file. The --output_path parameter can be any valid path.

Reference
=========
Ivanova, D. P., P. J. Gleckler, K. E. Taylor, P. J. Durack, and K. D. Marvel, 2016: Moving beyond the Total Sea Ice Extent in Gauging Model Biases. J. Climate, 29, 8965–8987, https://doi.org/10.1175/JCLI-D-16-0026.1. 
