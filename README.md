PCMDI metrics package
======
[![stable version](http://img.shields.io/badge/stable version-1.0.0-brightgreen.svg)](https://github.com/PCMDI/pcmdi_metrics/releases/tag/1.0.0)
![repo size](https://reposs.herokuapp.com/?path=PCMDI/pcmdi_metrics)
![platforms](http://img.shields.io/badge/platforms-linux | osx-lightgrey.svg)
[![DOI](http://img.shields.io/badge/DOI-10.5281/zenodo.xxxxx-orange.svg)](http://doi.org/10.5281/zenodo.xxxxx)

SUMMARY
-------

The PCMDI metrics package is used to objectively compare results from climate models with observations using well-established statistical tests. Results are produced in the context of all model simulations that have been contributed to CMIP5 and earlier phases of CMIP.  Among other purposes, this enables modeling groups to exaluate performance changes during the development cycle in the context of the structural error distribution in the multi-model ensemble. Currently, the comparisons are focused on large- to global-scale annual cycle performance metrics.

The metrics package consists of four parts: 1) Analysis software, 2) an observationally-based database of global (or near global, land or ocean) annual cycle climatologies, 3) a database of performance metrics computed for all CMIP models and 4) package documentation.


GETTING STARTED
----------------

Installation requirements and instructions are available at: https://github.com/PCMDI/pcmdi_metrics/wiki/Install

Some installation support for modeling groups participating in CMIP is available via pcmdi-metrics@llnl.gov

Once the package has been successfully installed, the user needs to configure his/her environment to run the package with one of the following two commands, depending on their shell environment:

```> source {install_prefix}/PCMDI_METRICS/bin/setup_runtime.sh```

or

```> source {install_prefix}/PCMDI_METRICS/bin/setup_runtime.csh```

NOTE:  The environment must be set for every window where the metrics package is executed.

Once the environment is set up, some basic tests of the package can be run to verify everything is properly configured.  

```> pcmdi_metrics_driver.py -p {install_prefix}/PCMDI_METRICS/test/pcmdi/basic_test_parameters_file.py```

This will have produced some test results in tos_2.5x2.5_esmf_linear_metrics.json which can be compared with expected results: 

```> diff {install_prefix}/PCMDI_METRICS/test/pcmdi/tos_2.5x2.5_esmf_linear_metrics.json.good pcmdi_install_test_results/metrics_results/installationTest/tos_2.5x2.5_esmf_linear_metrics.json```

Once everything is ok, you can safely remove the temporary directory

```> rm -rf {install_prefix}/PCMDI_METRICS/tmp```


USING THE PCMDI METRICS PACKAGE
-----------------------------------

1) The user needs to prepare their model data so that it can be read by the metrics package.  A way this can be guaranteed is by following the CMIP/CF conventions. It is not necessary to use CMOR, but CF conventions need to followed.  The user can map their variable names to to those used in CMIP (see parameter file below), i.e., their data does not have to use the PCMDI variable names.  At present, PCMDIs metrics package expect climatological annual cycle data (12 months).

2) The user prepares an input parameter file (see below).  

3) The package is executed from the terminal prompt with something like:

```> pcmdi_metrics_driver.py -p MY_parameter_file.py```   

4) Results are output in JSON files which are easy to read and use. The results are organized as nested python dictionaries which are easy to acces and manipulate.  Examples are available in the file {install_prefix}/PCMDI_METRICS/doc/simple_json_test.py    


PREPARING THE INPUT PARAMETER FILE
----------------------------------

work in progress...
