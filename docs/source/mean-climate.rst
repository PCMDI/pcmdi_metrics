.. _using-the-package:

*****************
Mean Climate
*****************

Overview
========

The mean climate summary statistics are some of the most routine analysis available from the PMP.  At the same time, because of the number of options available they do require some preparation in advance of the analysis, including:

* Setting-up observational climatologies

* Preparation of model climatologies 

* Construction of an input parameter file  


Each of these steps are included in the `mean climate notebook <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_1_mean_climate.ipynb>`_ along with a series of examples that demonstrate the options. These steps are also summarized below.


Observational climatologies
###########################

A database of `observational climatologies is available to users of the PMP. To obtain this, please contact the PMP user group (pcmdi-metrics@llnl.gov) and you will be promptly provided with the database.  A subset of this database is available via the demo data made available for the PMP tutorials via a `jupyter notebook demo <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_0_download_data.ipynb>`_.  Once you have downloaded this demo data you can interactively run the mean climate and other demos.  

The PMP's mean climate summary statistics can be applied many fields and in most cases there is more than one reference data set available.  To accomodate this, as noted above the observational climatologies used by the PMP are managed via `a simple catalogue in the form of a JSON file <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/pcmdiobs2_clims_byVar_catalogue_v20201210.json>`_.  For many of the variables there are 'default' and 'alternate1' datasets and for some there is also an 'alternate2'.  Note: To simplify the use of the different options in the mean climate, the mean_climate_driver.py (see below) expects to be pointed to such a JSON file that summarizes the database. Currently, if a user wants to add additional observational data this can be done by including it in the JSON cataloge. Note: this most be done carefully to ensure the file retains compliant JSON structure.       


 
Preparation of model climatologies
##################################

Sample model climatologies are available as part of the PMP demo database noted above and are used for the mean climate notebook. However, if a user wants to create and use their own model climatologies the a simple example is provide in the mean climate notebook itself or the `PMP github repository <https://github.com/PCMDI/pcmdi_metrics/tree/master/sample_setups/pcmdi_parameter_files/mean_climate/make_clims>`_.   


Construction of an input paramater file
#######################################

The PMP mean climate metrics can be controlled via an input parameter file, the command line, or both.  With the command line only it is executed via: ::


   mean_climate_driver.py  -p basic_param.py

or as a combination of an input parameter file and the command line, e.g.: ::

   mean_climate_driver.py  -p basic_param.py --vars rlut pr 

where the list of variables (vars) to run the analysis on includes 'rlut' (outgoing TOA longwave radiation) and 'pr' (precipitation).  The following parameters need to be set by the user either in a parameter file or on the command line:  

* **vars**: a python list of variables to apply the summary statistics, e.g., ['pr', 'rlut', 'tas']
* **test_data_set**: a python list of runs or models, e.g., ['ACCESS-1-0', 'CESM1']
* **filename_template**: template that is applicable for the runs in test_data_set, e.g., "CMIP5.historical.%(model_version).r1i1p1.mon.%(variable).198101-200512.AC.v20190225.nc" where "model_version" and "variable" will include the lists in test_data_set and vars.
* **test_data_path**: the path/template where the test_data resides, e.g.: 
* **reference_data_set**: a python list that specifies 'default', 'alternate1', 'alternate2' or 'all', e.g., ['default']
* **reference_data_path**: the root path to the PMP climatology database
* **target_grid**:
* **regrid_tool**: options include 
* **metric_output_path**:

The output of the mean climate summary statistics are saved in a JSON file.  `An example result <https://github.com/PCMDI/pcmdi_metrics/blob/master/sample_setups/jsons/mean_climate/CMIP5/historical/v20190724/tas/ACCESS1-0.tas.CMIP5.historical.regrid2.2p5x2p5.v20190724.json>`_ demonstrates that multiple statistics are computed for different conditions including regions and seasons. The resulting JSON files include the data, software and hardware information on how the summary statistics.  


In addition to the minimum set of parameters noted above, the following additional options than can be controlled for the mean climate:

* Define a different set of regions to compute the statistics.
* Provide or estimate a land-sea mask 
* Define regional masking (e.g., global land-only, global ocean-only,tropical land)
* Select to output (or not) interpolated climatologies including masking
* Output results for each model into the same JSON file or into model-specific JSON files
 
