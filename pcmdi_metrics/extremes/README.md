# PMP Extremes Metrics

This documentation is a work in progress, and may change at any time.

## Inputs

Temperature: metrics in same units as input data. Must have variable "tasmax" or "tasmin"

Precipitation: inputs expected to be kg/m2/s. Converts to mm/day. Variable name must be pr,PRECT, or precip

The input data must use coordinates "lat" and "lon".

It is not required to provide a reference dataset

The default JSON output is designed to be cmec compliant - do not need to use CMEC flag.

If land/sea masks are not provided, there is an option to generate them on the fly using cdutil.

## Run
python pmp_extremes_driver.py -p parameter_file --other_params

## Outputs
This script will produce metrics JSONs and netcdf files (optional) containing block max/min values for temperature and/or precipitation. 

Data is masked to be over land only (50<=sftlf<=100)

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
| coords      | (list) Coordinate pair lists. The coordinate must be listed in consecutive order, as they would occur when walking the perimeter of the bounding shape. Does not need to be a box, but cannot have holes. Follows the pattern [[x1,y1],[x1,y2],[x2,y2],[x2,y1]].  |
| region_name | (str) Name of region. Default is "custom". |

## Time series settings

| Parameter   | Definition |
--------------|-------------
| dec_mode | (str) Toggle how season containing December, January, and February is defined. "DJF" or "JFD". Default "DJF". |
| annual_strict | (bool) This only matters for Rx5day. If True, only use data from within a given year in the 5-day means. If False, the rolling mean will include the last 4 days of the prior year. Default False. |
| drop_incomplete_djf | (bool) Don't include data from the first January/February and last December in the analysis. Default False. |

## Other parameters
| Parameter   | Definition |
--------------|-------------
| case_id |  (str) Will be appended to the metrics_output_path if present. | 
| model_list | (list) List of model names.  | 
| realization | (list) List of realizations. | 
| vars | (list) List of variables: "pr", "tasmax", and/or "tasmin". | 
| filename_template | (str) The template for the model file name. May contain placeholders %(variable), %(model), %(model_version), or %(realization) | 
| test_data_path  |  (str) The template for the directory containing the model file. May contain placeholders %(variable), %(model), %(model_version), or %(realization) | 
| sftlf_filename_template | (str) The template for the model land/sea mask file. May contain placeholders %(model), %(model_version), or %(realization) | 
| generate_sftlf | (bool) If true, generate a land/sea mask on the fly when the model or reference land/sea mask is not found. If false, skip datasets when land/sea mask is not found. | 
| reference_data_path | (str) The full path of the reference data file. | 
| reference_data_set  | (str) The short name of the reference datas set for labeling output files. | 
| reference_sftlf_template | (str) The full path of the reference data set land/sea mask. | 
| metrics_output_path  | (str) The directory to write output files to. | 
| nc_out | (bool) True to save yearly block extrema as netcdf files. | 
| debug | (bool) True to use debug mode. | 
| year_range |  (list) A list containing the start year and end year. | 



