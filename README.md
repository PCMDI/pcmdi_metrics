<div>
<img src="share/pcmdi/PMPLogo_1359x1146px_300dpi.png" height="90" align="right" />
<img src="share/pcmdi/PCMDILogo_400x131px_72dpi.png" height="60" align="right" />
</div>

<br><br><br><br>

# PCMDI Metrics Package (PMP)


[![latest version](https://anaconda.org/conda-forge/pcmdi_metrics/badges/version.svg)](https://anaconda.org/conda-forge/pcmdi_metrics/)
![Last updated](https://anaconda.org/conda-forge/pcmdi_metrics/badges/latest_release_date.svg)
![platforms](https://img.shields.io/badge/platforms-linux%20|%20osx-lightgrey.svg)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.592790.svg)](https://doi.org/10.5281/zenodo.592790)
[![License](https://anaconda.org/conda-forge/pcmdi_metrics/badges/license.svg)](https://github.com/PCMDI/pcmdi_metrics/blob/main/LICENSE)
[![Formatted with black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

Conda-forge (NEW, recommended):
[![Download](https://anaconda.org/conda-forge/pcmdi_metrics/badges/downloads.svg)](https://anaconda.org/conda-forge/pcmdi_metrics/)

PCMDI Conda Channel (halted):
[![Download](https://anaconda.org/pcmdi/pcmdi_metrics/badges/downloads.svg)](https://anaconda.org/pcmdi/pcmdi_metrics)

The PCMDI Metrics Package (PMP) is used to provide "quick-look" objective comparisons of Earth System Models (ESMs) with one another and available observations.  Results are produced in the context of all model simulations contributed to CMIP6 and earlier CMIP phases.  Among other purposes, this enables modeling groups to evaluate changes during the development cycle in the context of the structural error distribution of the multi-model ensemble. Currently, the comparisons emphasize metrics of large- to global-scale annual cycle, tropical and extra-tropical modes of variability, ENSO, MJO, regional monsoons, and high frequency characteristics of simulated precipitation.

**PCMDI uses the PMP to produce [quick-look simulation summaries across generations of CMIP](https://pcmdi.llnl.gov/research/metrics/).**

The metrics package consists of the following parts: 
* Analysis software
* Observation-based reference database of global (or near global, land or ocean) [time series and climatologies](https://github.com/PCMDI/PCMDIobs-cmor-tables/tree/master/catalogue)
* [Package documentation](http://pcmdi.github.io/pcmdi_metrics/) and [interactive jupyter notebook demos](https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/README.md)
* [Database](https://github.com/PCMDI/pcmdi_metrics_results_archive) of performance metrics computed for CMIP models

The package expects model data to be [CF-compliant](http://cfconventions.org/). To successfully use the package some input data "conditioning" may be required. We provide several demo scripts within the package.


Documentation
-------------

**Getting Started**

* Installation requirements and instructions are available on the [Install](http://pcmdi.github.io/pcmdi_metrics/install.html) page

* Users will need to contact the PMP developers (pcmdi-metrics@llnl.gov) to obtain supporting datasets and get started using the package.

* An overview for using the package and template scripts are detailed on the [Using-the-package](http://pcmdi.github.io/pcmdi_metrics) page

* [View Demo](https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/README.md)


Contact
-------

[Report Bug](https://github.com/PCMDI/pcmdi_metrics/issues)

[Request Feature](https://github.com/PCMDI/pcmdi_metrics/issues)

Some installation support for CMIP participating modeling groups is available: pcmdi-metrics@llnl.gov


Contributors
------------

Thanks to our contributors!

[![Contributors](https://contrib.rocks/image?repo=PCMDI/pcmdi_metrics)](https://github.com/PCMDI/pcmdi_metrics/graphs/contributors)



Acknowledgement
---------------
Content in this repository is developed by climate and computer scientists from the Program for Climate Model Diagnosis and Intercomparison ([PCMDI][PCMDI]) at Lawrence Livermore National Laboratory ([LLNL][LLNL]). This work is sponsored by the Regional and Global Model Analysis ([RGMA][RGMA]) program, of the Earth and Environmental Systems Sciences Division ([EESSD][EESSD]) in the Office of Biological and Environmental Research ([BER][BER]) within the [Department of Energy][DOE]'s [Office of Science][OS]. The work is performed under the auspices of the U.S. Department of Energy by Lawrence Livermore National Laboratory under Contract DE-AC52-07NA27344.

<p>
    <img src="https://github.com/PCMDI/assets/blob/main/DOE/480px-DOE_Seal_Color.png?raw=true"
         width="65"
         style="margin-right: 30px"
         title="United States Department of Energy"
         alt="United States Department of Energy"
    >&nbsp;
    <img src="https://github.com/PCMDI/assets/blob/main/LLNL/212px-LLNLiconPMS286-WHITEBACKGROUND.png?raw=true"
         width="65"
         title="Lawrence Livermore National Laboratory"
         alt="Lawrence Livermore National Laboratory"
    >
</p>


[PCMDI]: https://pcmdi.llnl.gov/
[LLNL]: https://www.llnl.gov/
[RGMA]: https://climatemodeling.science.energy.gov/program/regional-global-model-analysis
[EESSD]: https://science.osti.gov/ber/Research/eessd
[BER]: https://science.osti.gov/ber
[DOE]: https://www.energy.gov/
[OS]: https://science.osti.gov/



License
-------

Distributed under the BSD 3-Clause License. See [`LICENSE`](https://github.com/PCMDI/pcmdi_metrics/blob/main/LICENSE) for more information.


Release Notes and History
-------------------------

[Released versions](https://github.com/PCMDI/pcmdi_metrics/releases)

- [v3.0.0](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.0.0) - New metric added: Cloud feedback by @mzelinka. [xCDAT](https://xcdat.readthedocs.io/en/latest/) implemented for mean climate metrics
- [v2.5.1](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.5.1) - Technical update
- [v2.5.0](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.5.0) - New metric added: Precipitation Benchmarking -- distribution. Graphics updated
- [v2.4.0](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.4.0) - New metric added: AMO in variability modes
- [v2.3.2](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.3.2) - CMEC interface updates
- [v2.3.1](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.3.1) - Technical update
- [v2.3](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.3) - New graphics using [archived PMP results](https://github.com/PCMDI/pcmdi_metrics_results_archive)
- [v2.2.2](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.2.2) - Technical update
- [v2.2.1](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.2.1) - Minor update
- [v2.2](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.2) - New metric implemented: precipitation variability across time scale
- [v2.1.2](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.1.2) - Minor update
- [v2.1.1](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.1.1) - Simplified dependent libraries and CI process
- [v2.1.0](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.1.0) - CMEC driver interfaced added.
- [v2.0](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.0) - New capabilities: ENSO metrics, demos, and documentations.
- [v1.2](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v1.2) - Tied to CDAT 8.0.  Now includes extensive regression testing.  New metrics: Diurnal cycle and intermittency of precipitation, sample monsoon metrics.
- [v1.1.2](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v1.1.2) - Now managed through Anaconda, and tied to UV-CDAT 2.10.  Weights on bias statistic added.   Extensive provenance information incorporated into json files.
- [v1.1](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v1.1) - First public release, emphasizing climatological statistics, with development branches for ENSO and regional monsoon precipitation indices.
- [v1.0](https://github.com/PCMDI/pcmdi_metrics/releases/tag/v1.0) - Prototype version of the PMP.
