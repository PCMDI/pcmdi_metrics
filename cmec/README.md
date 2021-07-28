README

# Mean Climate
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

# Modes of variability  
1. Edit settings in cmec.json.  
    `modpath` and `reference_data_path` are relative to the CMEC $CMEC_MODEL_DATA and $CMEC_OBS_DATA directories, respectively.  
    The `ObsUnitsAdjust` and `ModUnitsAdjust` tuples should be encased in quotes (e.g. `"ObsUnitsAdjust": "(True, 'divide', 100.0)"`)  
2. Move or link observational data to your chosen "obs" dir  
3. Move or link model data to your chosen "model" dir   
4. Run cmec driver: `python cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/variability_modes`  

# MJO
1. Edit settings in cmec.json  
2. Move or link observational data to your chosen "obs" dir  
3. Move or link model data to your chosen "model" dir  
4. Run cmec driver: `python cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/mjo`  

# Monsoon (Wang)
1. Edit settings in cmec.json.  
    `test_data_path` and `reference_data_path` are relative to the CMEC $CMEC_MODEL_DATA and $CMEC_OBS_DATA directories, respectively.  
    The `threshold` variable needs to be in the same units as your input data. The default is 2.5 mm / 86400 = 2.894e-05 for model input with  units of kg m-2 s-1.  
2. Move or link observational data to your chosen "obs" dir  
3. Move or link model data to your chosen "model" dir  
4. Run cmec driver: `python cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/monsoon_wang` 

# Monsoon (Sperber)
1. Edit settings in cmec.json  
    `modpath` and `reference_data_path` are relative to the CMEC $CMEC_MODEL_DATA and $CMEC_OBS_DATA directories, respectively.  
    `modpath_lf` and `reference_data_lf` path are also relative to the above directories.  
    The `ObsUnitsAdjust` and `ModUnitsAdjust` tuples should be encased in quotes (e.g. `"ObsUnitsAdjust": "(True, 'divide', 100.0)"`)  
3. Move or link observational data to your chosen "obs" dir  
4. Move or link model data to your chosen "model" dir  
5. Run cmec driver: python `cmec-driver.py run -obs <obs dir> <model dir> <output dir> PMP/monsoon_sperber`  

# Diurnal Cycle of Precipitation
1. Edit settings in cmec.json
    `filename_template` is relative to your $CMEC_MODEL_DATA directory. This should be 3hr precipitation data.  
    Do not set `modpath` as this is your $CMEC_MODEL_DATA directory.
2. Move or link model data to your chosen "model" dir   
3. Run cmec driver: `python cmec-driver.py run <model dir> <output dir> PMP/diurnal_cycle`  

## Running multiple metrics
Follow all but the final step for your chosen metrics. To run all the metrics via cmec-driver, run:  
`cmec-driver.py run -obs <obs dir> <model dir> <output dir> <list metrics names>`  
For example:
`python cmec-driver.py run -obs obs model output PMP/mjo PMP/monsoon_wang PMP/diurnal_cycle`  

## Other tips for the configuration file
True and False values in the JSON standard are represented by `true` and `false`. For the PMP metrics, users can also use the strings `"True"` and `"False"`, though this is not recommended.  
The PMP parameter files accept python functions and datatypes that are not valid JSON objects. Any parameter values that are function calls, tuples, or other non-JSON types should be encased in quotes.  
The "datetime", "glob", and "os" packages are available in the parameter files generated during this workflow. These packages can be used to set parameter values in cmec.json. For example, a user can set `"case_id": "datetime.datetime.now().strftime('v%Y%m%d')"` to have the case_id reflect the date.    
