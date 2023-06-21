.. pcmdi_metrics documentation master file, created by
   sphinx-quickstart on Wed Nov  4 13:15:37 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

***************************
PCMDI Metrics Package (PMP)
***************************

The Program for Climate Model Diagnosis & Intercomparison (`PCMDI`_) Metrics Package (PMP) is used to provide "quick-look" objective comparisons of Earth System Models (ESMs) with one another and available observations.  
Results are produced in the context of all model simulations contributed to CMIP6 and earlier CMIP phases.  
Currently, the comparisons emphasize metrics of large- to global-scale annual cycle and both tropcial 
and extra-tropical modes of variability. 
Recent release (v3) include established statistics for mean climate, ENSO, MJO, extratropical modes of variability, 
regional monsoons, and high frequency characteristics of simulated precipitation as a part of U.S. DOE's Benchmarking of simulated precipitation. 

`PCMDI`_ uses the PMP to produce `quick-look simulation summaries across generations of CMIP <https://pcmdi.llnl.gov/metrics>`_.

The PMP expects model data to be `CF-compliant <http://cfconventions.org/>`_, otherwise, 
to successfully use the package may require some input data conditioning. 
It is also strongly suggested to work with observation datasets following the `CF-compliant <http://cfconventions.org/>`_, 
such as datasets from the `obs4MIPs`_ project. 


Getting Started
===============
Installation requirements and instructions are available on the :ref:`install` page

An overview of the summary statistics available via the package 
are summarized with interactive Jupyter notebooks in the :ref:`metrics` page

Some installation support for CMIP participating modeling groups is available: pcmdi-metrics@llnl.gov


Acknowledgement
===============

Huge thank you to all of the PMP `contributors`_!

.. _contributors: https://github.com/PCMDI/pcmdi_metrics#contributors

PMP is developed by scientists and developers from the Program for Climate Model Diagnosis and
Intercomparison (`PCMDI`_) at Lawrence Livermore National Laboratory (`LLNL`_). 
This work is sponsored by the Regional and Global Model Analysis (`RGMA`_) program of 
the Earth and Environmental Systems Sciences Division (`EESSD`_) in 
the Office of Biological and Environmental Research (`BER`_) 
within the `Department of Energy`_'s `Office of Science`_. 
The work is performed under the auspices of the U.S. Department of Energy by 
Lawrence Livermore National Laboratory under Contract DE-AC52-07NA27344.

.. _LLNL: https://www.llnl.gov/
.. _PCMDI: https://pcmdi.llnl.gov/
.. _RGMA: https://climatemodeling.science.energy.gov/program/regional-global-model-analysis
.. _EESSD: https://science.osti.gov/ber/Research/eessd
.. _BER: https://science.osti.gov/ber
.. _Department of Energy: https://www.energy.gov/
.. _Office of Science: https://science.osti.gov/
.. _obs4MIPs: https://pcmdi.github.io/obs4MIPs/


License
=======

BSD 3-Clause License. See `LICENSE <https://github.com/PCMDI/pcmdi_metrics/blob/main/LICENSE>`_ for details

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: For users:

   overview
   start
   metrics
   Results <https://pcmdi.llnl.gov/research/metrics/>

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: For developers/contributors:

   resources
   team
   GitHub repository <https://github.com/PCMDI/pcmdi_metrics>

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Community

   GitHub discussions <https://github.com/PCMDI/pcmdi_metrics/discussions>