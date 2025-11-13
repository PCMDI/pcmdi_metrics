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

## Region Masking
Users can provide a shapefile, column name, and name to mask data over a desired region using in the parameter file. 

```
shp_path = "/path/to/shapefile/cb_2018_us_state_20m.shp"
attribute = "NAME"
region_name = "California"
```

## Parameters:
| Parameter   | Definition |
--------------|-------------
| case_id |  (str) Will be appended to the metrics_output_path if present. | 
| realization | (list) List of model realizations. | 
| vars | (list) List of variables: "pr", "tasmax", and/or "tasmin". | 
| test_data_set | (list) List of model (or observation) names to be compared to the reference dataset. | 
| filename_template | (str) The template for the model file name. May contain placeholders %(variable), %(model), %(model_version), or %(realization), or wildcards like "?" or "*" | 
| test_data_path  | (str) The template for the directory containing the model file. May contain placeholders %(variable), %(model), %(model_version), or %(realization), or wildcards like "?" or "*" | 
| reference_data_set | (list) List of reference dataset names, e.g. ["Livneh"]
| reference_filename_template | (str) The template for the reference file name. May contain placeholders %(variable) or wildcards like "?" or "*" | 
| reference_data_path | (str) The template for the directory containing the reference file. May contain placeholders %(variable) or wildcards like "?" or "*" |
| sftlf_filename_template | (str) The template for the model land/sea mask file. May contain placeholders %(model), %(model_version), or %(realization), or wildcards like "?" or "*". Takes precedence over --generate_sftlf | 
| generate_sftlf | (bool) If true, generate a land/sea mask on the fly using natural_earth_v5_0_0.land_110 when no model or reference land/sea mask is found. If false, no land/sea mask is applied. | 
| shp_path    |  (str) path to shapefile.  |
| attribute      | (str) Attribute used to identify region (eg, column of attribute table). For example, "COUNTRY" in a shapefile of countries.  |
| region_name | (str) Unique feature value of the region that occurs in the attribute given by "--attribute". Must match only one geometry in the shapefile. An example is "NORTH_AMERICA" under the attribute "CONTINENTS". |
| metrics_output_path  | (str) The directory to write output files to. |  
| plots | (bool) True to save metric maps. |
| nc_out | (bool) True to save netcdf files (required for postprocessing). |
| msyear | (int) Start year for model data set. |
| meyear | (int) End year for model data set. |
| osyear | (int) Start year of the observation dataset |
| oeyear | (int) End year of the observation dataset. If no reference dataset is given, osyear and oeyear must be a subset of msyear and meyear. This temporal range will be used as the "Reference" dataset for comparison metrics |
| ModUnitsAdjust | (dict) Provide information for units conversion for each variable in vars. Uses format {var: (flag (bool), operation (str), value (float), new units (str))}. Operation can be "add", "subtract", "multiply", or "divide". For example, use {"pr": (True, 'multiply', 86400, 'mm/day')} to convert kg/m2/s to mm/day.|
| ModUnitsAdjust | (dict) Provide information for units conversion for each variable in reference dataset vars. Uses format {var: (flag (bool), operation (str), value (float), new units (str))}. Operation can be "add", "subtract", "multiply", or "divide". For example, use {"pr": (True, 'multiply', 86400, 'mm/day')} to convert kg/m2/s to mm/day.|
| annual_strict | (bool) This only matters for rolling 5-day metrics. If True, only use data from within a given year in the 5-day means. If False, the rolling mean will include the last 4 days of the prior year. Default False. |
| custom_thresholds | (dict) Custom values used for threshold metrics. Different units than found in ModUnitsAdjust or ObsUnitsAdjust can be used For example, set {"tasmin_ge", {"values": [70], "units": "degF"}} to calculate the number of days with tasmin greater than or equal to 70 Fahrenheit. Default values can be found in drcdm/param/default_thresholds.txt |
| include_metrics | (list) List of metrics to calculate. Leave out of param file to compute all metrics. A full metric list can be found in drcdm/param/full_metric_list.txt. You may also set include_metrics to a variable name ("pr", "tasmax", etc.) to run all metrics associated with that variable. The given variable must be within vars parameter. 
| compute_tasmean | (bool) If true and tasmax and tasmin are provided, calculate daily mean temperature using $tas = \frac{(tasmax + tasmin)}{2}$ and compute mean temperature metrics. 


## Key information

### Units
The temperature data must be converted to Fahrenheit, Kelvin, or Celcius. The ModUnitsAdjust parameter can be used to convert either Kelvin or Celsius units to Fahrenheit on-the-fly. See this example:

```
ModUnitsAdjust_precip = (True, "multiply", 86400.0 / 25.4, "inches")  # Convert model units from kg/m2/s to mm/day
ObsUnitsAdjust_precip = (True, "multiply", 1 / 25.4, "inches")

ModUnitsAdjust_temperature = (True, "KtoF", 0, "F")  # Set to False to Leave in K
ObsUnitsAdjust_temperature = (True, "CtoF", 0, "F")

ModUnitsAdjust = {
    v: ModUnitsAdjust_precip if "pr" in v else ModUnitsAdjust_temperature for v in vars
}
ObsUnitsAdjust = {
    v: ObsUnitsAdjust_precip if "pr" in v else ObsUnitsAdjust_temperature for v in vars
}

```
Precipitation units must be provided in mm or inches. ModUnitsAdjust can also be used as documented in the Parameters section to convert units such as kg/m2/s to mm.

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

# For developers
Some testing and issues have been documented in the original DRCDM PR: https://github.com/PCMDI/pcmdi_metrics/pull/1131
