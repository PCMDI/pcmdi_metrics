# PMP Extremes Metrics

## Inputs

The Extremes Driver works on daily gridded climate data. This package expects input netcdf files to be cf-compliant and on regular latitude/longitude grids. X and Y dimensions must be named "lon" and "lat", and the time dimension must be named "time". The input variables must be called "tasmax", "tasmin", or "pr". Input files must contain lat, lon, and time bounds.

### Reference data
A reference (observation) input is not required, but it is necessary to create Taylor Diagrams. Reference data sets must follow the above rules for variable names and bounds.

### Land/sea mask
Block extrema and return values will only be generated over land areas, so a land/sea mask is required for all datasets. Land is defined as grid cells where the land area percentage is between 50 and 100. Areas south of 50S will be masked out.

If available, users should provide the land/sea mask that accompanies their datasets. The mask variable in the land/sea mask file must be called "sftlf". If land/sea masks are scaled from 0-1, they will be rescaled to 0-100 on-the-fly. If land/sea masks are not provided, there is an option to generate them on-the-fly using pcmdi_utils. See "Other Parameters" for more information.

### Covariate data and stationarity
The extremes driver can produce nonstationary return values for model-only runs. To generate nonstationary return values, users must provide a covariate file path and name (see "Other Parameters" for these settings). If no covariate file is provided, the Extremes Driver will generate stationary return values.

The covariate file must contain an annual time series of the covariate variable. Covariate data must be provided in a netcdf file with time bounds included. The covariate time dimension must either 1) be exactly the same length in years as the input data, or 2) overlap in years with the input data time dimension. It is recommended that a log transformation be applied to nonlinear time series such as recent carbon dioxide values.

### Other options
See the "Other Parameters" table for options to select a year range, convert units, and control regridding.

## Run

To run the extremes metrics, use the following command format in a PMP environment:  
```extremes_driver.py -p parameter_file --other_params```

## Outputs
The outputs will be written to a single directory. This directory will be created by the driver if it does not already exist. Otherwise, the output directory should be empty before the driver starts. The name of the output directory is controlled by the `metrics_output_path` and `case_id` parameters. 

This script will produce metrics JSONs, netcdf files, and figures (optional). There will be netcdf files containing block max/min values for temperature and/or precipitation, along with return value and standard error files. A metadata file called "output.json" will be generated with more detailed information about the files in the output bundle. Return value statistics will be provided for stationary return values only.

All netcdf files will contain data for 5 time periods: Annual ("ANN"), DJF, MAM, JJA, and SON. Data is masked to be over land only (50<=sftlf<=100). Antarctica is excluded.

If multiple realizations are provided for a single model, a single return value file will be produced for that model which makes use of all provided realizations in the return value computation.

### Metrics
Metrics are produced to describe the time mean extrema values, along with spatial statistics comparing the mean model field to mean observed field. Metrics are output for Annual, DJF, MAM, JJA, and SON seasons.
Model only: "mean", "std_xy"  
If reference dataset is available: "mean", "std_xy", "std-obs_xy", "pct_dif", "bias_xy", "cor_xy", "mae_xy", "rms_xy", "rmsc_xy"  

## Regional Analysis

You can either use a region from a shapefile or provide coordinate pairs that define the region. Consult the parameters section for more information.

## Parameters

### Shapefile 

| Parameter   | Definition |
--------------|-------------
| shp_path    |  (str) path to shapefile.  |
| attribute      | (str) Attribute used to identify region (eg, column of attribute table). For example, "COUNTRY" in a shapefile of countries.  |
| region_name | (str) Unique feature value of the region that occurs in the attribute given by "--attribute". Must match only one geometry in the shapefile. An example is "NORTH_AMERICA" under the attribute "CONTINENTS". |

### Coordinates 
| Parameter   | Definition |
--------------|-------------
| coords      | (list) Coordinate lat/lon pair lists. The coordinate must be listed in consecutive order, as they would occur when walking the perimeter of the bounding shape. Does not need to be a box, but cannot have holes. For example [[lat1,lon1],[lat1,lon2],[lat2,lon2],[lat2,lon1]].  |
| region_name | (str) Name of region. Default is "custom". |

## Time series settings

| Parameter   | Definition |
--------------|-------------
| dec_mode | (str) Toggle how season containing December, January, and February is defined. "DJF" or "JFD". Default "DJF". |
| annual_strict | (bool) This only matters for Rx5day. If True, only use data from within a given year in the 5-day means. If False, the rolling mean will include the last 4 days of the prior year. Default False. |
| drop_incomplete_djf | (bool) If True, don't include data from the first January/February and last December in the analysis. Default False. |

## Other parameters
| Parameter   | Definition |
--------------|-------------
| case_id |  (str) Will be appended to the metrics_output_path if present. | 
| model_list | (list) List of model names.  | 
| realization | (list) List of realizations. | 
| vars | (list) List of variables: "pr", "tasmax", and/or "tasmin". | 
| filename_template | (str) The template for the model file name. May contain placeholders %(variable), %(model), %(model_version), or %(realization) | 
| test_data_path  |  (str) The template for the directory containing the model file. May contain placeholders %(variable), %(model), %(model_version), or %(realization) | 
| sftlf_filename_template | (str) The template for the model land/sea mask file. May contain placeholders %(model), %(model_version), or %(realization). Takes precedence over --generate_sftlf | 
| generate_sftlf | (bool) If true, generate a land/sea mask on the fly when the model or reference land/sea mask is not found. If false, skip datasets when land/sea mask is not found. | 
| reference_data_path | (str) The full path of the reference data file. | 
| reference_data_set  | (str) The short name of the reference datas set for labeling output files. | 
| reference_sftlf_template | (str) The full path of the reference data set land/sea mask. | 
| metrics_output_path  | (str) The directory to write output files to. |  
| covariate_path | (str) File path of covariate timeseries netcdf. |
| covariate | (str) Name of covariate variable in file given by --covariate_path. |
| plots | (bool) True to save world map figures of mean metrics. |
| debug | (bool) True to use debug mode. | 
| msyear | (int) Start year for model data set. |
| meyear | (int) End year for model data set. |
| osyear | (int) Start year for reference data set. |
| oeyear | (int) End year for model data set. |
| regrid | (bool) Set to False to skip regridding if all datasets are on the same grid. Default True. |  
| ModUnitsAdjust | (tuple) Provide information for units conversion. Uses format (flag (bool), operation (str), value (float), new units (str)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 86400, 'mm/day') to convert kg/m2/s to mm/day.|
| ObsUnitsAdjust | (tuple) Similar to ModUnitsAdjust, but for reference dataset. |  

## Extreme value analysis details

For this driver, we have implemented the Generalized Extreme Value analysis in pure Python. The return value results may vary from those obtained with the R climextRemes package, which was used to conduct the return value analysis in Wehner, Gleckler, and Lee (2000). In the nonstationary case, the GEV location parameter is linearly dependent on the covariate. 

## References

Michael Wehner, Peter Gleckler, Jiwoo Lee, 2020: Characterization of long period return values of extreme daily temperature and precipitation in the CMIP6 models: Part 1, model evaluation, Weather and Climate Extremes, 30, 100283, https://doi.org/10.1016/j.wace.2020.100283.
