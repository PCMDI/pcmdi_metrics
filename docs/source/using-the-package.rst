.. _using-the-package:

*****************
Using the Package
*****************

GETTING STARTED
===============

Installation requirements and instructions are available at: https://github.com/PCMDI/pcmdi_metrics/wiki/Install

Some installation support for modeling groups participating in CMIP is available via pcmdi-metrics@llnl.gov

To verify the PMP environment is successfully set up, try the following at the unix command prompt ($): ::

$ which python

This should point you to something like: {HOMEDIRECTORY}/anaconda2/bin/python, where the {HOMEDIRECTORY} is where you installed the PMP using the anaconda instructions.  If instead you are pointed to /usr/bin/python, this is the default python installed on your computer and it means the PMP is not yet recognized in your current window.  If that is the case, make sure anaconda is in your ${PATH} and if necessary revisit the instructions for installing the PMP with Anaconda.     

Next try: ::

$ which pcmdi_metrics_driver.py

If this file is found, there is a good chance you have your PMP environment set up properly, so you can proceed to working with some of the demos below.

USER GUIDE PMP v1.1
===================
(in progress, last updated May 31, 2016)

Overview
--------

The PMP uses the Python programming language and the Ultrascale Visualization Climate Data Analysis Tools (UV-CDAT), a powerful software tool kit that provides cutting-edge climate diagnostic and visualization capabilities. It can be set up for users unfamiliar with Python and UV-CDAT to test their own models with some help from the PMP developers (pcmdi-metrics@llnl.gov). However, users with a little Python experience will have access to a wide range of analysis capabilities and more readily be able to adapt the PMP functions for their own purposes. **Users of the current release (v1.1) will need to contact the PMP developers (pcmdi-metrics@llnl.gov) to get started, obtain access to the PMP observational database, and set up the package for their application.**
The primary functionality of the PMP v1.1 is to compute a wide range of climatological statistics and relate them to the CMIP multi-model ensemble. Well-established ENSO and monsoon statistics are in a development repository that will soon be merged with the master repository. A critical design constraint of the PMP is that it is closely aligned with the data standards and conventions of CMIP. Coupled with the capabilities of UV-CDAT, this offers a powerful and extensible analysis framework that can be readily extendable and will serve as a basis for systematic characterization of all CMIP DECK and historical simulations.

Usage
-----

Steps to start using the v.1.1 package include:

1.	Install the PMP
2.	Ensure your simulation output is structured similar to CMIP and obtain the PMP observational database from the PMP developers.
3.	Prepare a test “input parameter file” to read input model data and observations, select which variables to test, and where to output the results (see demo examples below)
4.	Once a parameter file is successfully set up the PMP can be executed, providing summary statistics output as JSON files (http://www.json.org/) 
5.	The output (JSON files) can be used to produce plots that compare models with observations and other CMIP simulations, either with the user’s preferred plotting tools or those provided with the PMP.


Preparing model data for use with the PMP
-----------------------------------------

The key to being able to operate the PMP is that all climate model output must closely match the data conventions of CMIP. If a model’s output was processed with CMOR, it will almost certainly be readably by the PMP. Without this, there are a number of technical details a user will have to be cognizant of to ensure their data can be read by the PMP. There is some flexibility - it is possible for a user to keep their own variable names and units. The primary analysis in the PMP v1.1 is on the climatological annual cycle, and it is currently assumed a user already routinely computes these (code for this will be provided in v1.2). It is expected that the 12-month climatological time series is in a single netCDF file with variable dimensions (12, latitude, longitude) starting in January and ending in December. In v1.1 the PMP relies on the time index (0-11 in Python) in the climatologies so the datum and units of the time axis are not important.  

If the 12 month annual cycle climatology is not in a single file, there is a powerful UV-CDAT utility (cdscan) included in the PMP that can be used to “span in time” across multiple files. cdscan is a command line operation that can be used to create an xml that can be read by the PMP (via CDMS).   See http://uvcdat.llnl.gov/documentation/cdms/cdms_7.html

The PMP observational database is organized very similar to how CMIP model output is organized on the ESGF.  Users should contact the PMP developers (pcmdi-metrics@llnl.gov) to obtain a copy.  Additional datasets can be added to the database provided they are done so in a way that adheres to the directory structure of the database.  Once they are added, for local execution of the PMP a simple script (https://github.com/PCMDI/pcmdi_metrics/blob/master/src/python/pcmdi/scripts/build_obs_meta_dictionary.py) needs to be updated and executed.  For collaborators wishing to contribute new observations into the master PMP, a GIT branch should be created with a pull request.

With the model and observational data are properly structured and organized, the next step is to set up a parameter file. This parameter file is a python ".py" file where the user specifies the file/directory structure of both the model and observational data as well as the variables for which the user wants to compute summary statistics. There are other options set in this file such as the target grid resolution, whether or not the user wants to save the interpolated climatologies, compute statistics over ocean only, etc.   Output is saved as a “json” file, an internationally recognized lightweight data-interchange format that is easy to read and write (json.org).  For our purposes, it is especially powerful as a simple database for organizing the summary statistics computed by the PMP and enabling them to be easily read in python.  
As example script is provided described in the demo package described below.   

Demos
=====

Running the PMP climate statistics
----------------------------------

The PMP v1.1 summary statistics are executed with a parameter file as follows: ::

$  pcmdi_metrics_driver.py -p /MY_PATH/my_parameter_file.py

Where “my_parameter_file.py” is your customized input parameter file and “MY_PATH” is the location of the parameter file.  

Before setting up your own input parameter file, we suggest you run our first demo which highlights the function of parameter file with a simple test case, and then uses this to execute the PMP.  With the PMP properly installed, you should be able to execute the following command: ::

$ pmp_demo_1.py

As part of running this demo a tar file with model and observational data for the demo will be downloaded from http://oceanonly.llnl.gov/gleckler1/pmp-demo-data/pmpv1.1_demodata.tar 


Reading the summary statistics produced by the PMP
--------------------------------------------------


A sample script for reading in PMP results is available on the PMP github repository:
https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/simple_json_test.py

