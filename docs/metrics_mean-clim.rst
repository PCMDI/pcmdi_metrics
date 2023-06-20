*****************
Mean Climate
*****************

Overview
========

The mean climate summary statistics are the most routine analysis available from the PMP.
Because they are quasi-operationally applied to large numbers of simulations and under 
different conditions, the current mode of opertation is fairly general.  
Before it can be applied some prepration is needed including:    

* Setting-up observational climatologies

* Construction of model climatologies 

* Construction of an input parameter file to run the desired operations  


Each of these steps are included in the 
`mean climate notebook <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_1_mean_climate.ipynb>`_ 
along with a series of examples that demonstrate the options. 
These steps are also summarized below.


Observational climatologies
###########################

A subset of the observational climatologies used for the PMP's 
mean climate metrics is available via a `jupyter notebook demo <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_0_download_data.ipynb>`_.
Once you have run this demo or downloaded this demo data you can interactively 
run the mean climate and other demos.  
The complete database of observational climatologies is available to users of the PMP. 
To obtain this, please contact the PMP user group (pcmdi-metrics@llnl.gov) 
and you will be promptly provided with the database.

The PMP's mean climate summary statistics can be applied to many fields and 
in most cases there is more than one reference data set available.  
To accomodate this, the observational climatologies used by the PMP a
re managed via `a simple catalogue in the form of a JSON file <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/pcmdiobs2_clims_byVar_catalogue_v20201210.json>`_.  
For many of the variables there are 'default' and 'alternate1' 
datasets and for some there is also an 'alternate2'.  
To simplify the use of the different options in the mean climate, 
the mean_climate_driver.py (see below) expects to be pointed to observational catalogue.  
Currently, if a user wants to add additional observational data this can be done by 
including it in the JSON cataloge. However, this most be done carefully to ensure 
the file retains JSON compliant structure.       

A recent observational climatology catalogue is included as part of the PMP as a default, so it does not need to be explicitly idenified when using the mean_climate_driver.py (unless the catalogue has been modified to include new observations). However, as described below, the user must provide the base path to the observational database. As indicated in the catalogue, the actual database does incorporate futher directory structure and defined filenames which should not be modified.  If changes are made to the catalogue, this can be done with input parameter settings (below) using the "custom_observations" option.     

 
Preparation of model climatologies
##################################

Sample model climatologies are available as part of the PMP demo database noted above 
and are used for the mean climate notebook. However, if a user wants to create and use 
their own model climatologies with the PMP a simple example is provide in a stand 
alone `climatology notebook <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_1a_compute_climatologies.ipynb>`_, 
via the `mean climate metrics notebook <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_1_mean_climate.ipynb>`_, 
or the `PMP github repository <https://github.com/PCMDI/pcmdi_metrics/tree/master/sample_setups/pcmdi_parameter_files/mean_climate/make_clims>`_.   


Construction of an input paramater file
#######################################

The PMP mean climate metrics can be controlled via an input parameter file, the command line, or both.  With the command line only it is executed via: ::


   mean_climate_driver.py  -p basic_param.py

or as a combination of an input parameter file and the command line, e.g.: ::

   mean_climate_driver.py  -p basic_param.py --vars rlut pr 

where the list of variables (vars) to run the analysis on includes 'rlut' (outgoing TOA longwave radiation) and 'pr' (precipitation).  The following parameters are **required to be set by the user** either in a parameter file or on the command line:  

* **vars**: a python list of variables to apply the summary statistics, e.g., ['pr', 'rlut', 'tas']
* **test_data_set**: a python list of runs or models, e.g., ['ACCESS-1-0', 'CESM1']
* **filename_template**: template that is applicable for the runs in test_data_set, e.g., "CMIP5.historical.%(model_version).r1i1p1.mon.%(variable).198101-200512.AC.v20190225.nc" where "model_version" and "variable" will be analyzed for each of the entries in test_data_set and vars.
* **test_data_path**: the path/template where the test_data resides, e.g.: 
* **reference_data_set**: a python list that specifies 'default', 'alternate1', 'alternate2' or 'all', e.g., ['default']
* **reference_data_path**: the root path to the observational climatology database, e.g., '~/demo_data/PCMDIobs2_clims/'
* **target_grid**: '2.5x2.5' or an actual cdms2 grid object
* **regrid_tool**: options include 'esmf' and 'regrid2'  
* **metric_output_path**: the full path to the metrics output in JSON files, e.g., '~/demo_data/PMP_metrics/' 

In addition to the above required input parameters, if the default cataolgue of observational climatologies is not being used its replacement needs to be specified, e.g.: ::

    custom_observations = './pcmdiobs2_clims_byVar_catalogue_v20200615.json'


The output of the mean climate summary statistics are saved in a JSON file.  `An example result <https://github.com/PCMDI/pcmdi_metrics/blob/master/sample_setups/jsons/mean_climate/CMIP5/historical/v20190724/tas/ACCESS1-0.tas.CMIP5.historical.regrid2.2p5x2p5.v20190724.json>`_ demonstrates that multiple statistics are computed for different conditions including regions and seasons. The resulting JSON files include the data, software and hardware information on how the summary statistics.  


In addition to the minimum set of parameters noted above, the following **additional options can be controlled** for the mean climate:

* **cmec** Flag to save summary statistics into a CMEC compliant JSON file or not.  
* **region_specs** Define a different set of domains to compute the statistics (python dictionary).
* **regions** Specify which domains are applied to which variables (python dictionary).
* **sftlf_filename_template** Provided a land-sea mask to be used in defining regions.
* **generate_sftlf** Estimate a land-sea mask.
* **save_test_clims** Select to save (or not) interpolated climatologies including masking
* **case_id** Save JSON and netCDF files into a subdirectory so that results from multiple tests can be readily organized
 
