# Decision Relevant Climate Data Metrics

# How to run:
Install the PCMDI Metrics Package.

Set up a parameter file with your model information. An example parameter file can be found at param/drcdm_param.py. See the Parameters section below for more information.

Run the decision relevant metrics driver using the following command:
```
drcdm_driver.py -p your_parameter_file.py
```

## Inputs
The Decision Relevant Metrics Driver works on daily gridded climate data. This package expects input netcdf files to be cf-compliant and on regular latitude/longitude grids. X and Y dimensions must be named "lon" and "lat", and the time dimension must be named "time". The input variables must be called "tasmax", "tasmin", or "pr". Input files must contain lat, lon, and time bounds.

## Land/Sea mask
Metrics should only be calculated over land, so users have the option to provide a land/sea mask if the ocean area are not already masked in the input data. If the land/sea mask contains fractional values, land will defined as grid cells where the land area percentage is between 50 and 100. Areas south of 50S will be masked out.

If available, users should provide the land/sea mask that accompanies their datasets. The mask variable in the land/sea mask file must be called "sftlf". If land/sea masks are not provided, there is an option to generate them on-the-fly using pcmdi_utils. If no mask is provided and --generate-sftlf is set to False, no masking will be done by the PMP.

## Parameters:
| Parameter   | Definition |
--------------|-------------
| case_id |  (str) Will be appended to the metrics_output_path if present. | 
| model_list | (list) List of model names.  | 
| realization | (list) List of realizations. | 
| vars | (list) List of variables: "pr", "tasmax", and/or "tasmin". | 
| filename_template | (str) The template for the model file name. May contain placeholders %(variable), %(model), %(model_version), or %(realization) | 
| test_data_path  |  (str) The template for the directory containing the model file. May contain placeholders %(variable), %(model), %(model_version), or %(realization) | 
| sftlf_filename_template | (str) The template for the model land/sea mask file. May contain placeholders %(model), %(model_version), or %(realization). Takes precedence over --generate_sftlf | 
| generate_sftlf | (bool) If true, generate a land/sea mask on the fly when the model or reference land/sea mask is not found. If false, no land/sea mask is applied. | 
| metrics_output_path  | (str) The directory to write output files to. |  
| plots | (bool) True to save world map figures of mean metrics. |
| nc_out | (bool) True to save netcdf files (required for postprocessing). |
| msyear | (int) Start year for model data set. |
| meyear | (int) End year for model data set. |
| ModUnitsAdjust | (tuple) Provide information for units conversion. Uses format (flag (bool), operation (str), value (float), new units (str)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 86400, 'mm/day') to convert kg/m2/s to mm/day.|
| dec_mode | (str) Toggle how season containing December, January, and February is defined. "DJF" or "JFD". Default "DJF". |
| annual_strict | (bool) This only matters for rolling 5-day metrics. If True, only use data from within a given year in the 5-day means. If False, the rolling mean will include the last 4 days of the prior year. Default False. |
| drop_incomplete_djf | (bool) If True, don't include data from the first January/February and last December in the analysis. Default False. |
| shp_path    |  (str) path to shapefile.  |
| attribute      | (str) Attribute used to identify region (eg, column of attribute table). For example, "COUNTRY" in a shapefile of countries.  |
| region_name | (str) Unique feature value of the region that occurs in the attribute given by "--attribute". Must match only one geometry in the shapefile. An example is "NORTH_AMERICA" under the attribute "CONTINENTS". |

## Key information

### Units
The temperature data must be provided in Fahrenheit. The ModUnitsAdjust parameter can be used to convert either Kelvin or Celsius units to Fahrenheit on-the-fly. See this example:

```
# Kelvin to Fahrenheit
ModUnitsAdjust = (True, 'KtoF', 0, 'F')

# Celsius to Fahrenheit
ModUnitsAdjust = (True, 'CtoF', 0, 'F')
```
Precipitation units must be provided in mm. ModUnitsAdjust can also be used as documented in the Parameters section to convert units such as kg/m2/s to mm.

### Regions
The most efficient way to get postprocessed metrics for multiple regions is to run the drcdm driver without any region subsetting (leave shp_path, attribute, and region_name unset). The regions can be applied during postprocessing.

## Interquartile range script

After running the drcdm_driver over an ensemble for the variables pr, tasmax, and tasmin, users have the optional to produced an interquartile range table using the script scripts/iqr.py. This script is hard-coded to use the NCA5 CONUS regions.

| Parameter   | Definition |
--------------|-------------
| filename_template | (str) The template for the model DRCDM results. May contain placeholder %(variable). A wildcard must be used in place of model name or realization name. | 
| reference_template | (str) The template for the reference DRCDM results. May contain placeholder %(variable). A wildcard must be used in place of model name or realization name. |
| output_path | (str) Output directory for iqr.py results (optional). |
| shapefile_path | (str) Full path to the NCA5 regions shapefile. |
| obs_name | (str) Name of the reference data, for example, "PRISM". |
| model_name | (str) Name of the model data, for example, "LOCA2". |

For example, a user's PMP DRCDM model results are stored at /home/userid/LOCA2. They organized by variable, model, and realization, so the  results for GFDL-CM4 r1i1p1f1 precipitation are found at /home/userid/LOCA2/pr/GFDL-CM4/r1i1p1f1. The user's `filename_template` variable would then be formatted as "/home/userid/LOCA2/%(variable)/\*/\*/".

This script will write JSON files for ensemble mean statistics (relative and absolute differences between ensemble mean and reference dataset) and a csv file containing the values for the interquartile range table.

# How to test:
Create a conda environment with pcmdi_metrics and xclim
In the PMP root directory use:
`pip install .`

Edit the metrics output path in pcmdi_metrics/drcdm/param/drcdm_param.py to be a location at which you have write permission.

To launch a run with the demo parameter file use:
`drcdm_driver.py -p pcmdi_metrics/drcdm/param/drcdm_param.py`
