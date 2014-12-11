PCMDI metrics package
======
[![stable version](http://img.shields.io/badge/stable version-1.0.0-brightgreen.svg)](https://github.com/PCMDI/pcmdi_metrics/releases/tag/1.0.0)
![repo size](https://reposs.herokuapp.com/?path=PCMDI/pcmdi_metrics)
![platforms](http://img.shields.io/badge/platforms-linux | osx-lightgrey.svg)
[![DOI](http://img.shields.io/badge/DOI-10.5281/zenodo.xxxxx-orange.svg)](http://doi.org/10.5281/zenodo.xxxxx)

The PCMDI metrics package is used to objectively compare results from climate models with observations using well-established statistical tests. Results are produced in the context of all model simulations contributed to CMIP5 and earlier CMIP phases.  Among other purposes, this enables modeling groups to evaluate changes during the development cycle in the context of the structural error distribution of the multi-model ensemble. Currently, the comparisons are focused on large- to global-scale annual cycle performance metrics.

The metrics package consists of four parts: 1) Analysis software, 2) an observationally-based database of global (or near global, land or ocean) annual cycle climatologies, 3) a database of performance metrics computed for CMIP models and 4) package documentation.

The package expects model data to be [CF-compliant](http://cfconventions.org/). To successfully use the package some input data "conditioning" may be required. We provide a number of demo scripts within the package to facilitate new users.

GETTING STARTED
----------------

Installation requirements and instructions are available on the [Install](https://github.com/PCMDI/pcmdi_metrics/wiki/Install) page

An overview for using the package and template scripts are detailed on the [Using-the-package](https://github.com/PCMDI/pcmdi_metrics/wiki/Using-the-package) page

Some installation support for CMIP participating modeling groups is available: pcmdi-metrics@llnl.gov