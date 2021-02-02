.. _using-the-package:

*****************
Mean Climate
*****************

Overview
========

The mean climate summary statistics are some of the most routine analysis available from the PMP.  At the same time, because of the number of options available they do require some preparation in advance of the analysis, including:

* Setting observational climatologies

* Preparation of model climatologies 

* Construction of an input parameter file  

Observational climatologies
###########################

A database of `observational climatologies <https://github.com/PCMDI/PCMDIobs-cmor-tables/blob/master/catalogue/pcmdiobs2_clims_byVar_catalogue_v20201210.json>`_ is available to users of the PMP. To obtain this, please contact the PMP user group (pcmdi-metrics@llnl.gov) and you will be promptly provided with the database.  A subset of this database is available via the demo data made available for the PMP tutorials via a `jupyter notebook demo <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_0_download_data.ipynb>`_.  Once you have downloaded this demo data you can interactively run the mean climate and other demos.  

The `mean climate notebook <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_1_mean_climate.ipynb>`_ provides a series of examples that demonstrate the options available.  
 
Preparation of model climatologies
##################################

Sample model climatologies are available as part of the PMP demo database noted above and are used for the mean climate notebook. However, if a user wants to create and use their own model climatologies the a simple example is provide in the mean climate notebook itself or the `PMP github repository <https://github.com/PCMDI/pcmdi_metrics/tree/master/sample_setups/pcmdi_parameter_files/mean_climate/make_clims>`_.   


Construction of an input paramater file
#######################################

The PMP mean climate metrics can be controlled via an input parameter file, the command line, or both.  With the command line only it is executed via: ::


   mean_climate_driver.py  -p basic_param.py

or as a combination of an input parameter file and the command line, e.g.: ::

   mean_climate_driver.py  -p basic_param.py --vars rlut pr 

where the list of variables to run the analysis on includes the variables 'rlut' (outgoing TOA longwave radiation) and 'pr' (precipitation).  The following parameters need to be set by the user either in a parameter file or on the command line:  

* test_data_set
* vars
* reference_data_set
* target_grid
* regrid_tool
* filename_template
* test_data_path
* reference_data_path
* metric_output_path

The output of the mean climate summary statistics are saved in a JSON file.  `An example result <https://github.com/PCMDI/pcmdi_metrics/blob/master/sample_setups/jsons/mean_climate/CMIP5/historical/v20190724/tas/ACCESS1-0.tas.CMIP5.historical.regrid2.2p5x2p5.v20190724.json>`_ demonstrates that multiple statistics are computed for different conditions including regions and seasons. The resulting JSON files include the data, software and hardware information on how the summary statistics.  


In addition to the minimum set of parameters noted above, the following additional options than can be controlled for the mean climate:

* Select regridding method option
* Define a different set of regions to compute the statistics.
* Provide or estimate a land-sea mask 
* Define regional masking (e.g., global land-only, global ocean-only,tropical land)
* Select to output (or not) interpolated climatologies including masking
* Output results for each model into the same JSON file or into model-specific JSON files
 
