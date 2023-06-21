.. _overview:

***********
Overview
***********

The PMP provides a diverse suite of analysis utilities each of which produce summary statistics that gauge the consistency between climate model simulations and available observations.  
The primary application of the PMP is to evaluate simulations from the `Coupled Model Intercomparison Project (CMIP) <https://www.wcrp-climate.org/wgcm-cmip>`_.  
It can also be used to provide objective performance summaries during the model development process as well as selected research purposes.  
The notes below provide a brief summary of some of the key aspects of the PMP design.  

Software framework and dependancies
-----------------------------------

Most of the PMP is based on `Python 3 <https://www.python.org/>`_ and built upon the Climate Data Analysis Tools (`CDAT <https://cdat.llnl.gov>`_).  
The key component of CDAT used by the PMP is the Community Data Management System (`CDMS <https://cdms.readthedocs.io/en/latest/manual/cdms_1.html>`_) which provides access to a powerful collection of climate specific utilites, inclduing cdutil, genutil and cdtime.
To modernize, PMP is in transition to implement Xarray Climate Data Analysis Tools (`xCDAT`_) as its primary building block.


Input/Output format
-------------------

The PMP is designed to most readily handle model output that adheres to the `Climate-Forecast (CF) data conventions <https://cfconventions.org/>`_.  
More specifically, because the PMP is used to routinely analyze simulations contributed to CMIP it leverages `the data conventions developed in support of CMIP <https://pcmdi.llnl.gov/CMIP6/Guide/dataUsers.html>`_.  
Many modeling groups have a workflow that conforms to CMIP or is very similiar to it, making it possible to adapt the PMP to assist in the model development process. 

The PMP statistics are output in `JSON format <https://www.json.org/json-en.html>`_, and the underlying diagnostics from which they were derived are typically saved in `netCDF format <https://www.unidata.ucar.edu/software/netcdf>`_.


Basic Operation
---------------

The summary statistics available with the PMP can be run independently or as a collective (the later to be available via the next PMP version).  Here is a glimpse of how the mean climate statistics are executed from the unix command prompt: ::

    $ mean_climate_driver.py -p e3sm_parameterfile.py 

Because there are often multiple parameters to set before executing a PMP code, routine operation often involves setting these options in an "input parameter" python file such as the filename immediately following the "-p" flag above.  The PMP input parameter files are similiar to a "namelist" text file used in other climate analysis packages but having the input parameters set in a python file enables us to leverage the power of python. For example, the contents of an input parameter file might look something like this: ::

    $ more input_parameters.py
    $ test_data_set = ['ACCESS-1-0','CESM2']
    $ period = '1981-2005'

which includes both a string variable (period) and a python list (test_data_set). Other python objects can be included in input parameter files, notably python dictionaries.  Additional functionality is shown in another example command: ::

   $ mean_climate_driver.py -p e3sm_parameterfile.py --variable pr 

Here, the "---variable" option is used to specify "pr" (precipitation) with other options included in the file after the "-p" flag.  


The python standard `argparse libary <https://docs.python.org/3/library/argparse.html>`_  is implicitly used in all cases, enabling the inclusion of user-friendly interface options.  As in the above example, this allows users to set input parameters on the command line **or** in an input file.  However, there are circumstances where users of the PMP may want to use a combination of both (an input parameter file and command line setting) for the same execution. This useful combination is possible with the standard argeparse library however with limited functionality.  We make use of the Community Diagnostics Package (`CDP <https://github.com/CDAT/cdp>`_) to enable prioritization between the two input possibilities.  The CDP enables us to use command line options in combination with input parameter files, with the command line inputs overrridding options set in the parameter files.  This provides convenience in setting up and maintaining large jobs. Examples of the combined use of parameter files and command line inputs are included in the PMP demos.

.. _xCDAT: https://xcdat.readthedocs.io/en/stable/