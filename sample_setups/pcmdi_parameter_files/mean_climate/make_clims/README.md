
CURRENTLY OPERATIONAL 
---------------------

nohup parallelize_driver.py --driver pcmdi_compute_climatologies.py -p cmip_clims_param.py > cmip5.amip.
rad.v20200423.txt &

As an alternative to using dask via the parallelize_driver, an equivalent simple parallelization can be accomplished as follows:

THIS IS NOT WORKING!


Additionally, pcmdi_compute_climatologies.py, includes an option to use CMOR to write climatologies, and to store climatological time bounds that reflect the actual time coordinate.  However, neither of these options are currently in use, and their inclusion considerably complicates this script.  Efforts are underway to simplify the climatology code (below).


PROTOTYPING /EZCLIM (requires additional development)
-------------------
python basicClim.py -p basicClim_inputparam.py


PROTOTYPING /EZCLIM2 (requires additional development)
--------------------

