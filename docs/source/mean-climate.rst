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

where the list of variables to run the analysis on includes the variables 'rlut' (outgoing TOA longwave radiation) and 'pr' (precipitation).  

Because there are a minimum of 5(?) parameters to be set with the mean climate statistics.    

SOME DISCUSSION HERE ON THE MINIMUM SET OF INPUT PARAMETERS.



In addition to the minimum set of parameters noted above, the following summarizes additional options than can be controlled for the mean climate:


* Select regridding option
* Define a different set of regions
* Provide or estimate a land-sea mask
* Define regional masking (e.g., land-only or ocean-only)
* Select to output (or not) interpolate climatologies including masking

 
