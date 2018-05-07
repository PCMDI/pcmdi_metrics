<img src="share/pcmdi/PMPLogo_1359x1146px_300dpi.png" width="50%" height="50%" />
<h5 align="right"></h5> 

PCMDI metrics package (PMP)
======
[![stable version](https://img.shields.io/badge/stable%20version-1.1.2-brightgreen.svg)](https://github.com/PCMDI/pcmdi_metrics/releases/tag/1.1.2)
![repo size](https://reposs.herokuapp.com/?path=PCMDI/pcmdi_metrics)
![platforms](https://img.shields.io/badge/platforms-linux%20|%20osx-lightgrey.svg)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.809463.svg)](https://doi.org/10.5281/zenodo.809463)
[![Anaconda-Server Badge](https://anaconda.org/pcmdi/pcmdi_metrics/badges/installer/conda.svg)](https://conda.anaconda.org/pcmdi)
[![Anaconda-Server Badge](https://anaconda.org/pcmdi/pcmdi_metrics/badges/downloads.svg)](https://anaconda.org/pcmdi/pcmdi_metrics)


The PCMDI metrics package is used to objectively compare results from climate models with observations using well-established statistical tests. Results are produced in the context of all model simulations contributed to CMIP5 and earlier CMIP phases.  Among other purposes, this enables modeling groups to evaluate changes during the development cycle in the context of the structural error distribution of the multi-model ensemble. Currently, the comparisons emphasize large- to global-scale annual cycle performance metrics. Current work in v1.x development branches include established statistics for ENSO, regional monsoon precipitation, and the diurnal cycle of precipitation. These diagnostics will be included in a future PMP release.

The metrics package consists of four parts: 1) Analysis software, 2) an observationally-based database of global (or near global, land or ocean) annual cycle climatologies, 3) a database of performance metrics computed for CMIP models and 4) package documentation.
The package expects model data to be [CF-compliant](http://cfconventions.org/). To successfully use the package some input data "conditioning" may be required. We provide several demo scripts within the package to facilitate new users.

**Users of the current release (v1.1.2) will need to contact the PMP developers (pcmdi-metrics@llnl.gov) to obtain supporting datasets and get started using the package.**


GETTING STARTED
----------------

Installation requirements and instructions are available on the [Install](https://github.com/PCMDI/pcmdi_metrics/wiki/Install) page

An overview for using the package and template scripts are detailed on the [Using-the-package](https://github.com/PCMDI/pcmdi_metrics/wiki/Using-the-package) page

Some installation support for CMIP participating modeling groups is available: pcmdi-metrics@llnl.gov


PMP versions
------------

v1.0 - Prototype version of the PMP

v1.1 - First public release, emphasizing climatological statistics, with development branches for ENSO and regional monsoon precipitation indices

v1.1.2 - Now managed through Anaconda, and tied to UV-CDAT 2.10.  Weights on bias statistic added.   Extensive provenance information incorporated into json files.
