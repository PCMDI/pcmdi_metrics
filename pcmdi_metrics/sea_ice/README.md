# Sea Ice

## Summary

The PCMDI Metrics Package (PMP) sea ice driver produces metrics that compare modeled and observed sea ice extent.

## Demo

* Link to notebook

## Inputs

The sea ice driver uses monthly mean sea ice concentration and grid area data to generate sea ice extent metrics. An unlimited number of test data sets (typically model data) may be provided, along with a single reference data set (typical observations or a model control run). See the Parameters section for more details about inputs.

## Run

The PMP sea ice metrics can be controlled via an input parameter file, the command line, or both. With the command line only it is executed via:

```
sea_ice_driver.py -p parameter_file.py
```

or as a combination of an input parameter file and the command line, e.g.:

```
sea_ice_driver.py -p parameter_file.py --msyear 1991 --meyear 2020
```

## Outputs

The driver produces a JSON file containing mean square error metrics for all input models and realizations relative to the reference data set. It also produces a bar chart displaying these metrics.

### Sectors

The metrics results are provided for eight different geographic regions. In the Northern Hemisphere there are the Arctic, North Pacific, North Atlantic, and Central Arctic regions. In the Southern Hemisphere there are the Antarctic, South Pacific, South Atlantic, and Indian Ocean regions. The region definitions can be found in Ivanova (2016).

## Parameters

* **case_id**: Save JSON and figure files into this subdirectory so that results from multiple tests can be readily organized.
* **test_data_set**: List of model names.
* **realization**: List of realizations.
* **test_data_path**: File path to directory containing model/test data.
* **filename_template**: File name template for test data, e.g., "CMIP5.historical.%(model_version).r1i1p1.mon.%(variable).19810-200512.AC.v2019022512.nc" where "model_version" and "variable" will be analyzed for each of the entries in test_data_set and vars.
* **var**: Name of model sea ice variable
* **msyear**: Start year for test data set.
* **meyear**: End year for test data set.
* **ModUnitsAdjust**: Factor to convert model sea ice data to fraction of 1. Uses format (flag (bool), operation (str), value (float)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 1e-2) to convert from percent concentration to decimal concentration.
* **area_template**: File path of model grid area data.
* **area_var**: Name of model area variable, e.g. "areacello"
* **AreaUnitsAdjust**: Factor to convert model area data to units of km2. Uses format (flag (bool), operation (str), value (float)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 1e6) to convert from m2 to km2.
* **metrics_output_path**: Directory path for metrics output in JSON files, e.g., '~/demo_data/PMP_metrics/'. The %(case_id) variable can be used here. If exists, should be empty before run.
* **reference_data_path_nh**: The reference data file path for the northern hemisphere. If data is global, provide same path for nh and sh.
* **reference_data_path_sh**: The reference data file path for the southern hemisphere. If data is global, provide same path for nh and sh.
* **ObsUnitsAdjust**: Factor to convert reference sea ice data to fraction of 1. Uses format (flag (bool), operation (str), value (float)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 1e-2) to convert from percent concentration to decimal concentration.
* **reference_data_set**: A short name describing the reference dataset, e.g. "OSI-SAF".
* **osyear**: Start year for reference data set.
* **oeyear**: End year for reference data set.
* **obs_var**: Name of reference sea ice variable.
* **ObsAreaUnitsAdjust**: Factor to convert model area data to units of km2. Uses format (flag (bool), operation (str), value (float)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 1e6) to convert from m2 to km2.
* **obs_area_template**: File path of grid area data. If unavailalbe, skip and use "obs_cell_area".
* **obs_area_var**: Name of reference area variable, if available. If unavailable, skip and use "obs_cell_area".
* **obs_cell_area**: For equal area grids, the area of a single grid cell in units of km2.


## Reference

Ivanova, D. P., P. J. Gleckler, K. E. Taylor, P. J. Durack, and K. D. Marvel, 2016: Moving beyond the Total Sea Ice Extent in Gauging Model Biases. J. Climate, 29, 8965–8987, https://doi.org/10.1175/JCLI-D-16-0026.1. 