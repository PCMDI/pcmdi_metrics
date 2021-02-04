.. pcmdi_metrics documentation master file, created by
   sphinx-quickstart on Wed Nov  4 13:15:37 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

***************************
PCMDI Metrics Package (PMP)
***************************

*The content of this site is currently being expanded to include examples for all of the PMP summary statistic functionality*

The PMP is used to provide "quick-look" objective comparisons of Earth System Models (ESMs) with one another and available observations.  Results are produced in the context of all model simulations contributed to CMIP6 and earlier CMIP phases.  Currently, the comparisons emphasize metrics of large- to global-scale annual cycle and both tropcial and extra-tropical modes of variability. Ongoing work in v1.x development branches include established statistics for ENSO, MJO, regional monsoons, and high frequency characteristics of simulated precipitation. 

PCMDI uses the PMP to produce `quick-look simulation summaries across generations of CMIP <https://cmec.llnl.gov/results/physical.html>`_


The PMP expects model data to be `CF-compliant <http://cfconventions.org/>`_, otherwise, to successfully use the package may require some input data conditioning. 

A suite of demo scripts and interactive Jupyter notebooks are provided with this documentation. 

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   Technical-overview
   install
   Supporting-data
   metrics-overview
   pmpparser


GETTING STARTED
===============
Installation requirements and instructions are available on the :ref:`install` page

An overview of the summary statistics available via the package are summarized with interactive Jupyter notebooks in the :ref:`metrics-overview` page

Some installation support for CMIP participating modeling groups is available: pcmdi-metrics@llnl.gov

PMP versions 
============

v1.2 - Tied to CDAT 8.0.  Now includes extensive regression testing.  New metrics: Diurnal cycle and intermittency of precipitation, Sperber and Wang Monsoon metrics

v1.1.2 - Now managed through Anaconda, and tied to UV-CDAT 2.10.  Weights on bias statistic added.   Extensive provenance information incorporated into json files.

v1.1 - First public release, emphasizing climatological statistics, with development branches for ENSO and regional monsoon precipitation indices

v1.0 - Prototype version of the PMP
