Technical Overview
***********

Summary
=======

The PMP provides a diverse suite of analysis utilities each of which produce summary statistics that gauge the consistency between climate model simulations and available observations.  The primary application of the PMP is to evaluate simulations from the `Coupled Model Intercomparison Project (CMIP) <https://www.wcrp-climate.org/wgcm-cmip>`_.  It can also be used to provide objective performance summaries during the model development process as well as selected research purposes.  The notes below provide a brief summary of some of the key aspects of the PMP design.  

Software framework and dependancies
-----------------------------------

Most of the PMP is based on `Python 3 <https://www.python.org/>`_ and built upon the Climate Data Analysis Tools (`CDAT <https://cdat.llnl.gov>`_).  The key component of CDAT used by the PMP is the Community Data Management System (`CDMS <https://cdms.readthedocs.io/en/latest/manual/cdms_1.html>`_) which provides access to a powerful collection of climate specific utilites, inclduing cdutil, genutil and cdtime.           


Input/Output format
-------------------

The PMP is designed to most readily handle model output that adheres to the `Climate-Forecast (CF) data conventions <https://cfconventions.org/>`_.  More specifically, because the PMP is used to routinely analyze simulations contributed to CMIP it leverages `the data conventions developed in support of CMIP <https://pcmdi.llnl.gov/CMIP6/Guide/dataUsers.html>`_.  Many modeling groups have a workflow that conforms to CMIP or is very similiar to it, making it possible to adapt the PMP to assist in the model development process. 

The PMP statistics are output in `JSON format <https://www.json.org/json-en.html>`_, and the underlying diagnostics from which they were derived are typically saved in `netCDF format <https://www.unidata.ucar.edu/software/netcdf>`_.


Basic Operation
---------------

The summary statistics available with the PMP can be run independently or as a collective (the later to be available via the next PMP version).  Here is a simple mock-up example of how argeparse is used from the unix command prompt ($): ::

$ mean_climate_driver.py -p e3sm_parameterfile.py 

Because there are often many parameters to set before executing a PMP code, routine operation often involves setting the input options in an "input parameter" python file such as the file following the "-p" flag.  This is similiar to a "namelist" text file used in other climate analysis packages but having the input parameters set in a python file enables us to leverage the power of python. The contents of this file might look something like this ($): ::

$ more input_parameters.py
$ model CESM2
$ variable pr


Additional functionality is shown in another example command ($): ::

$ mean_climate_driver.py -p e3sm_parameterfile.py --variable pr 

Here, the "---variable" option is used to specify "pr" (precipitation) with other options included in the file after the "-p" flag.  


The python standard `argparse libary <https://docs.python.org/3/library/argparse.html>`_  is used in all cases, enabling the inclusion of user-friendly interface options.  As in the above examples, this enables us to set input parameters on the command line or in an input file.  However, there are circumstances where users of the PMP may want to use a combination of both (command line and input file) for the same execution with the command line overriding anything set in the parameter file. To enable this option we make use of the Community Diagnostics Package (`CDP <https://github.com/CDAT/cdp>`_).  The ability to use command line options in combination with input parameter files (with the former overrridding options set in the later) provides a tremendous convenience in setting up large jobs.



