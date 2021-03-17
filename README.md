<img src="share/pcmdi/PMPLogo_1359x1146px_300dpi.png" width="15%" height="15%" align="right" />
<h5 align="right"></h5> 

PCMDI metrics package (PMP)
======
[![stable version](https://img.shields.io/badge/stable%20version-1.2-brightgreen.svg)](https://github.com/PCMDI/pcmdi_metrics/releases/tag/1.2)
![platforms](https://img.shields.io/badge/platforms-linux%20|%20osx-lightgrey.svg)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.809463.svg)](https://doi.org/10.5281/zenodo.809463)
[![Anaconda-Server Badge](https://anaconda.org/pcmdi/pcmdi_metrics/badges/installer/conda.svg)](https://conda.anaconda.org/pcmdi)
[![Anaconda-Server Badge](https://anaconda.org/pcmdi/pcmdi_metrics/badges/downloads.svg)](https://anaconda.org/pcmdi/pcmdi_metrics)
[![CircleCI](https://circleci.com/gh/PCMDI/pcmdi_metrics.svg?style=svg)](https://circleci.com/gh/PCMDI/pcmdi_metrics)
[![Coverage Status](https://coveralls.io/repos/github/PCMDI/pcmdi_metrics/badge.svg)](https://coveralls.io/github/PCMDI/pcmdi_metrics)

The PCMDI metrics package is used to provide "quick-look" objective comparisons of Earth System Models (ESMs) with one another and available observations.  Results are produced in the context of all model simulations contributed to CMIP6 and earlier CMIP phases.  Among other purposes, this enables modeling groups to evaluate changes during the development cycle in the context of the structural error distribution of the multi-model ensemble. Currently, the comparisons emphasize metrics of large- to global-scale annual cycle and both tropcial and extra-tropical modes of variability. Ongoing work in v1.x development branches include established statistics for ENSO, MJO, regional monsoons, and high frequency characteristics of simulated precipitation. 

**PCMDI uses the PMP to produce [quick-look simulation summaries across generations of CMIP](https://cmec.llnl.gov/results/physical.html)** 

The metrics package consists of four parts: 1) Analysis software, 2) an observationally-based database of global (or near global, land or ocean) [time series and climatologies](https://github.com/PCMDI/PCMDIobs-cmor-tables/tree/master/catalogue), 3) a database of performance metrics computed for CMIP models and 4) [package documentation and interactive demos](http://pcmdi.github.io/pcmdi_metrics/).

The package expects model data to be [CF-compliant](http://cfconventions.org/). To successfully use the package some input data "conditioning" may be required. We provide several demo scripts within the package.

Users of the current release (v1.2) will need to contact the PMP developers (pcmdi-metrics@llnl.gov) to obtain supporting datasets and get started using the package.


GETTING STARTED
----------------

Installation requirements and instructions are available on the [Install](http://pcmdi.github.io/pcmdi_metrics/install.html) page

An overview for using the package and template scripts are detailed on the [Using-the-package](http://pcmdi.github.io/pcmdi_metrics) page

Some installation support for CMIP participating modeling groups is available: pcmdi-metrics@llnl.gov

PMP versions
------------

v1.2 - Tied to CDAT 8.0.  Now includes extensive regression testing.  New metrics: Diurnal cycle and intermittency of precipitation, sample monsoon metrics

v1.1.2 - Now managed through Anaconda, and tied to UV-CDAT 2.10.  Weights on bias statistic added.   Extensive provenance information incorporated into json files.

v1.1 - First public release, emphasizing climatological statistics, with development branches for ENSO and regional monsoon precipitation indices

v1.0 - Prototype version of the PMP

