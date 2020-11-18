.. pcmdi_metrics documentation master file, created by
   sphinx-quickstart on Wed Nov  4 13:15:37 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

***************************
PCMDI metrics package (PMP)
***************************

The PCMDI metrics package is used to provide "quick-look" objective comparisons of Earth System Models (ESMs) with one another and available observations.  Results are produced in the context of all model simulations contributed to CMIP6 and earlier CMIP phases.  Currently, the comparisons emphasize metrics of large- to global-scale annual cycle and both tropcial and extra-tropical modes of variability. Ongoing work in v1.x development branches include established statistics for ENSO, MJO, regional monsoons, and high frequency characteristics of simulated precipitation. 

PCMDI uses the PMP to produce `quick-look simulation summaries across generations of CMIP <https://cmec.llnl.gov/results/physical.html>`_

The metrics package consists of four parts: 1) Analysis software, 2) an observationally-based database, 3) a database of performance metrics computed for CMIP models and 4) package documentation.

The package expects model data to be `CF-compliant <http://cfconventions.org/>`_. To successfully use the package some input data "conditioning" may be required. We provide several demo scripts within the package.

Users of the current release (v1.2) will need to contact the PMP developers (pcmdi-metrics@llnl.gov) to obtain supporting datasets and get started using the package.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   self
   install
   install-using-anaconda
   using-the-package
   ipsl-corner
   pmp-using-cdp-guide
   pmpparser


GETTING STARTED
===============
Installation requirements and instructions are available on the :ref:`install` page

An overview for using the package and template scripts are detailed on the :ref:`using-the-package` page

Some installation support for CMIP participating modeling groups is available: pcmdi-metrics@llnl.gov

PMP versions
============

v1.2 - Tied to CDAT 8.0.  Now includes extensive regression testing.  New metrics: Diurnal cycle and intermittency of precipitation, Sperber and Wang Monsoon metrics

v1.1.2 - Now managed through Anaconda, and tied to UV-CDAT 2.10.  Weights on bias statistic added.   Extensive provenance information incorporated into json files.

v1.1 - First public release, emphasizing climatological statistics, with development branches for ENSO and regional monsoon precipitation indices

v1.0 - Prototype version of the PMP
