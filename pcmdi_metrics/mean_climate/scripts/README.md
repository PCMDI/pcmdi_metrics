# Run PMP Mean Climate (PCMDI internal usage)

## Generate annual cycle files
* `allvars_parallel_mod_clims.py`: PCMDI internal script to generate annual cycle netCDF files as the first step for mean climate metrics calculation
* `mk_CRF_clims.py`: after clims have been calculated the cloud radiative forcing (CRF) clims need to be calculated by combining radiation variables

## Prepare run metrics calculations
* `get_all_MIP_mods_from_CLIMS.py`: Generate a json file that includes list of models, e.g., `all_mip_mods-v20230130.json`

## Calculate metrics
* Serial mode
  * mean_climate_driver.py -p ../param/pcmdi_MIP_EXP_pmp_parameterfile.py

## Merge individual JSON files
* post_process_merge_jsons.py
