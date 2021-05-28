README

# Mean Climate
1. Edit settings in cmec.json.
    There are a few parameters you do NOT need to set:
        reference_data_path is assumed to be $CMEC_OBS_DATA
        test_data_path is assumed to be $CMEC_MODEL_DATA
        metrics_output_path is assumed to be $CMEC_WK_DIR
2. Move or link observational data to your chosen "obs" dir
    For example:
    `ln -s PCMDIobs2_clims obs`
3. Move or link model data to your chosen "model"
    For example:
    `ln -s model_data_directory model`
4. If the observational data file structure has changed, edit the observational data catalogue. Put the path to the new catalogue in the "custom_observations" parameter in cmec.json.
5. Run cmec driver: python `cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/mean_climate`

# Modes of variability
1. Edit settings in cmec.json.
    "modpath" and "reference_data_path" are relative to the CMEC $CMEC_MODEL_DATA and $CMEC_OBS_DATA directories, respectively.
    The ObsUnitsAdjust and ModUnitsAdjust tuples should be encased in quotes (e.g. "(True, 'divide', 100.0)")
2. Move or link observational data to your chosen "obs" dir
3. Move or link model data to your chosen "model"
4. Run cmec driver: python `cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/variability_modes`

# MJO
1. Edit settings in cmec.json
2. Move or link observational data to your chosen "obs" dir
3. Move or link model data to your chosen "model"
4. Run cmec driver: python `cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/mjo`

## Running multiple metrics
Follow steps 1-4 for mean climate and 1-3 for modes of variability and MJO. To run all the metrics via cmec-driver, run:
`cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/mean_climate PMP/variability_modes PMP/mjo`

## Other tips for the configuration file
True and False values in the JSON standard are represented by `true` and `false`. For the PMP metrics, users can also use the strings `"True"` and `"False"`, though this is not recommended.
The PMP parameter files accept python functions and datatypes that are not valid JSON objects. Any parameter values that are function calls, tuples, or other non-JSON types should be encased in quotes.