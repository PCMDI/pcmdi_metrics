README
## CMEC driver
The cmec-driver software can be obtained from the [cmec-driver repository](https://github.com/cmecmetrics/cmec-driver). A [wiki](https://github.com/cmecmetrics/cmec-driver/wiki) provides more instructions about the installation and set up. While some instructions are provided below for running cmec-driver, the wiki has a more complete set of [workflow instructions](https://github.com/cmecmetrics/cmec-driver/wiki/PCMDI-Metrics-Package).

## Mean Climate
1. Edit settings in cmec.json.
    There are a few parameters you do NOT need to set:
        `reference_data_path` is assumed to be $CMEC_OBS_DATA
        `test_data_path` is assumed to be $CMEC_MODEL_DATA
        `metrics_output_path` is assumed to be $CMEC_WK_DIR
        Set `compute_climatologies: true` to generate on-the-fly AC files from timeseries.
2. Move or link observational data to your chosen "obs" dir
    For example:
    `ln -s PCMDIobs2_clims obs`
3. Move or link model data to your chosen "model" directory
    For example:
    `ln -s model_data_directory model`
4. If the observational data file structure has changed, edit the observational data catalogue. Put the path to the new catalogue in the `custom_observations` parameter in cmec.json.
5. Run cmec driver: `python cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/mean_climate`

## Modes of variability
1. Edit settings in cmec.json.
    `modpath` and `reference_data_path` are relative to the CMEC $CMEC_MODEL_DATA and $CMEC_OBS_DATA directories, respectively.
    The `ObsUnitsAdjust` and `ModUnitsAdjust` tuples should be encased in quotes (e.g. `"ObsUnitsAdjust": "(True, 'divide', 100.0)"`)
2. Move or link observational data to your chosen "obs" dir
3. Move or link model data to your chosen "model" dir
4. Run cmec driver: `python cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/variability_modes`

## MJO
1. Edit settings in cmec.json
2. Move or link observational data to your chosen "obs" dir
3. Move or link model data to your chosen "model" dir
4. Run cmec driver: `python cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/mjo`

## Monsoon (Wang)
1. Edit settings in cmec.json.
    `test_data_path` and `reference_data_path` are relative to the CMEC $CMEC_MODEL_DATA and $CMEC_OBS_DATA directories, respectively.
    The `threshold` variable needs to be in the same units as your input data. The default is 2.5 mm / 86400 = 2.894e-05 for model input with  units of kg m-2 s-1.
2. Move or link observational data to your chosen "obs" dir
3. Move or link model data to your chosen "model" dir
4. Run cmec driver: `python cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/monsoon_wang`

## Monsoon (Sperber)
1. Edit settings in cmec.json
    `modpath` and `reference_data_path` are relative to the CMEC $CMEC_MODEL_DATA and $CMEC_OBS_DATA directories, respectively.
    `modpath_lf` and `reference_data_lf` path are also relative to the above directories.
    The `ObsUnitsAdjust` and `ModUnitsAdjust` tuples should be encased in quotes (e.g. `"ObsUnitsAdjust": "(True, 'divide', 100.0)"`)
3. Move or link observational data to your chosen "obs" dir
4. Move or link model data to your chosen "model" dir
5. Run cmec driver: python `cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/monsoon_sperber`

## Diurnal Cycle of Precipitation
1. Edit settings in cmec.json
    `filename_template` is relative to your $CMEC_MODEL_DATA directory. This should be 3hr precipitation data.
    Do not set `modpath` as this is your $CMEC_MODEL_DATA directory.
2. Move or link model data to your chosen "model" dir
3. Run cmec driver: `python cmec-driver.py run <model dir> <output dir> PMP/diurnal_cycle`

### Running multiple metrics
Follow all but the final step for your chosen metrics. To run all the metrics via cmec-driver, run:
`cmec-driver.py run -obs <obs dir> <model dir> <output dir> <list metrics names>`
For example:
`python cmec-driver.py run -obs obs model output PMP/mjo PMP/monsoon_wang PMP/diurnal_cycle`
It is not guaranteed that the metrics will run in the same order that they are listed in your run statement.

### Other tips for the configuration file
True and False values in the JSON standard are represented by `true` and `false`. For the PMP metrics, users can also use the strings `"True"` and `"False"`, though this is not recommended.
The PMP parameter files accept python functions and datatypes that are not valid JSON objects. Any parameter values that are function calls, tuples, or other non-JSON types should be encased in quotes.
The "datetime", "glob", and "os" packages are available in the parameter files generated during this workflow. These packages can be used to set parameter values in cmec.json. For example, a user can set `"case_id": "datetime.datetime.now().strftime('v%Y%m%d')"` to have the case_id reflect the date.

# Information for Developers
This folder contains settings files and scripts as an interface between the PMP and cmec-driver. It is organized so that each metric is a standalone cmec-driver configuration within the PMP module. Each metric has its own folder containing a settings JSON, a driver script, and a metadata script. There is an additional "scripts" folder for shared code. Finally, there is a file called "contents.json" that is located at the top level of the PMP repo.

## How does the interface work
CMEC driver first looks at the contents.json file to find the settings file for the desired metric. It then checks the settings file "driver" key to find the driver to run. CMEC driver adds a call to the metric driver script to a script called "cmec_run.bash" which is created at runtime and located in the cmec-driver output folder for that metric. CMEC driver also writes environment variables pointing to the PMP code directory, obs data, model data, and conda information to "cmec_run.bash". If multiple metrics are run in the same cmec-driver run statement, the "cmec_run.bash" files are first created for all the metrics. CMEC driver then runs all the "cmec_run.bash" scripts sequentially.

## Steps for adding a new metric
1. Create a folder for the metric under cmec/.
2. Write a driver bash script for the metric. This script should contain the entire workflow for generating the metric, including activating the PMP conda environment, generating a parameter file, running the metric, and generating metadata, as needed (for example, see mean_climate/pmp_mean_climate_driver.sh.
3. Write a settings file (for example, see mean_climate/pmp_mean_climate.json):
- The required keys are "settings", "varlist", and "obslist".
- The required keys under settings are "name", "long_name", and "driver".
- Add the driver file path (relative to pcmdi_metrics/) to "settings":"driver".
- Under "default_parameters" it is recommended that you provide the full settings needed to run a sample case out-of-the-box, using the same sample data as the Demo jupyter notebook.
5. Add the settings file path to pcmdi_metrics/contents.json in the "contents" list.
6. If there is any special processing that needs to happen to the input parameters, add that code to scripts/pmp_param_generator.py
7. If any other scripts are created to help run the metric in cmec-driver, save them under scripts/ or in the metric folder.
8. If the metric does not output its own metadata JSON, write a script to generate one (for example, see mean_climate/mean_climate_output.py). This script should be included in the driver script workflow (for example, see mean_climate/pmp_mean_climate_driver.sh).
9. (Optional) Add an html page that displays the results of your metric.
10. Test by running your new metric in cmec-driver. Check that it produces the output files that you expect and that they are correctly documented in your output metadata file.
