<div>
<img src="share/pcmdi/PMPLogo_1359x1146px_300dpi.png" height="90" align="right" />
<img src="share/pcmdi/PCMDILogo_400x131px_72dpi.png" height="60" align="right" />
</div>

<br><br><br><br>

# PCMDI Metrics Package (PMP)

<!-- badges: start -->
[![latest version](https://img.shields.io/conda/vn/conda-forge/pcmdi_metrics.svg?kill_cache=1)](https://anaconda.org/conda-forge/pcmdi_metrics/)
[![Last updated](https://anaconda.org/conda-forge/pcmdi_metrics/badges/latest_release_date.svg?kill_cache=1)](https://anaconda.org/conda-forge/pcmdi_metrics/files)
![platforms](https://img.shields.io/badge/platforms-linux%20|%20osx-lightgrey.svg)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.592790.svg)](https://doi.org/10.5281/zenodo.592790)
[![License](https://anaconda.org/conda-forge/pcmdi_metrics/badges/license.svg)](https://github.com/PCMDI/pcmdi_metrics/blob/main/LICENSE)
[![Formatted with black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![All Contributors](https://img.shields.io/github/all-contributors/PCMDI/pcmdi_metrics?color=ee8449&style=flat-square)](#contributors)

Conda-forge (CURRENT, recommended):
[![Download](https://anaconda.org/conda-forge/pcmdi_metrics/badges/downloads.svg?kill_cache=1)](https://anaconda.org/conda-forge/pcmdi_metrics/)

PCMDI Conda Channel (old, deprecated):
[![Download](https://anaconda.org/pcmdi/pcmdi_metrics/badges/downloads.svg?kill_cache=1)](https://anaconda.org/pcmdi/pcmdi_metrics)

<!-- badges: end -->

The PCMDI Metrics Package (PMP) is used to provide "quick-look" objective comparisons of Earth System Models (ESMs) with one another and available observations.  Results are produced in the context of all model simulations contributed to CMIP6 and earlier CMIP phases.  Among other purposes, this enables modeling groups to evaluate changes during the development cycle in the context of the structural error distribution of the multi-model ensemble. Currently, the comparisons emphasize metrics of large- to global-scale annual cycle, tropical and extra-tropical modes of variability, ENSO, MJO, regional monsoons, high frequency characteristics of simulated precipitation, and cloud feedback.

**PCMDI uses the PMP to produce [quick-look simulation summaries across generations of CMIP](https://pcmdi.llnl.gov/research/metrics/).**

The metrics package consists of the following parts: 
* Analysis software
* Observation-based reference database of global (or near global, land or ocean) [time series and climatologies](https://github.com/PCMDI/PCMDIobs-cmor-tables/tree/master/catalogue)
* [Package documentation](http://pcmdi.github.io/pcmdi_metrics/) and [interactive jupyter notebook demos](https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/README.md)
* [Database](https://github.com/PCMDI/pcmdi_metrics_results_archive) of performance metrics computed for CMIP models

The package expects model data to be [CF-compliant](http://cfconventions.org/). To successfully use the package some input data "conditioning" may be required. We provide several demo scripts within the package.


Documentation
-------------

### Getting Started


* Installation requirements and instructions are available on the [Install](http://pcmdi.github.io/pcmdi_metrics/install.html) page

* Users will need to contact the PMP developers (pcmdi-metrics@llnl.gov) to obtain supporting datasets and get started using the package.

* An overview for using the package and template scripts are detailed on the [Using-the-package](http://pcmdi.github.io/pcmdi_metrics) page

* [View Demo](https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/README.md)


### References

Latest: 

* Lee, J., Gleckler, P. J., Ahn, M.-S., Ordonez, A., Ullrich, P. A., Sperber, K. R., Taylor, K. E., Planton, Y. Y., Guilyardi, E., Durack, P., Bonfils, C., Zelinka, M. D., Chao, L.-W., Dong, B., Doutriaux, C., Zhang, C., Vo, T., Boutte, J., Wehner, M. F., Pendergrass, A. G., Kim, D., Xue, Z., Wittenberg, A. T., and Krasting, J.: Systematic and objective evaluation of Earth system models: PCMDI Metrics Package (PMP) version 3, Geosci. Model Dev., 17, 3919–3948, https://doi.org/10.5194/gmd-17-3919-2024, **2024**. 

Earlier versions:

* Gleckler, P. J., Doutriaux, C., Durack, P. J., Taylor, K. E., Zhang, Y., Williams, D. N., Mason, E., and Servonnat, J.: A more powerful reality test for climate models, Eos T. Am. Geophys. Un., 97, https://doi.org/10.1029/2016eo051663, **2016**. 

* Gleckler, P. J., Taylor, K. E., and Doutriaux, C.: Performance metrics for climate models, J. Geophys. Res., 113, D06104, https://doi.org/10.1029/2007jd008972, **2008**. 


Contact
-------

[Report Bug](https://github.com/PCMDI/pcmdi_metrics/issues)

[Request Feature](https://github.com/PCMDI/pcmdi_metrics/issues)

Some installation support for CMIP participating modeling groups is available: pcmdi-metrics@llnl.gov


Acknowledgement
---------------
Content in this repository is developed by climate and computer scientists from the Program for Climate Model Diagnosis and Intercomparison ([PCMDI][PCMDI]) at Lawrence Livermore National Laboratory ([LLNL][LLNL]). This work is sponsored by the Regional and Global Model Analysis ([RGMA][RGMA]) program, of the Earth and Environmental Systems Sciences Division ([EESSD][EESSD]) in the Office of Biological and Environmental Research ([BER][BER]) within the [Department of Energy][DOE]'s [Office of Science][OS]. The work is performed under the auspices of the U.S. Department of Energy by Lawrence Livermore National Laboratory under Contract DE-AC52-07NA27344.

LLNL-CODE-2004137 

DOE CODE ID: #153383


<p>
    <img src="https://pcmdi.github.io/assets/PCMDI/100px-PCMDI-Logo-NoText-square-png8.png"
         width="65"
         style="margin-right: 30px"
         title="Program for Climate Model Diagnosis and Intercomparison"
         alt="Program for Climate Model Diagnosis and Intercomparison"
    >&nbsp;
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

| <div style="width:300%">[Versions]</div> | Update summary   |
| ------------- | ------------------------------------- |
| [v3.9.1]      | New capability (**new modes for modes of variability metrics: EA, SCA**) and technical update
| [v3.9]        | New capability (**Decision-Relevant metrics, Database access API**) and new demo notebooks
| [v3.8.2]      | Technical update
| [v3.8.1]      | Technical update with new figure (modes of variability multi-panel plot)
| [v3.8]        | New capability (**figure generation for ENSO**, xCDAT migration completed for **Monsoon Wang** with figure generation), major dependency update (`numpy` >= 2.0)
| [v3.7.2]      | Technical update
| [v3.7.1]      | Technical update with documentation improvements
| [v3.7]        | New capability (**figure generation for mean climate**) and technical update
| [v3.6.1]      | Technical update, additional QC repair functions
| [v3.6]        | New capability (**regional application of precip variability**) and technical update
| [v3.5.2]      | New capability (**QC**, **new modes for modes of variability metrics: PSA1, PSA2**) and technical update
| [v3.5.1]      | Technical update
| [v3.5]        | Technical update: MJO and Monsoon Sperber [xCDAT](https://xcdat.readthedocs.io/en/latest/) conversion
| [v3.4.1]      | Technical update
| [v3.4]        | Technical update: Modes of variability [xCDAT](https://xcdat.readthedocs.io/en/latest/) conversion
| [v3.3.4]      | Technical update
| [v3.3.3]      | Technical update
| [v3.3.2]      | Technical update
| [v3.3.1]      | Technical update
| [v3.3]        | New metric added: **Sea-Ice**
| [v3.2]        | New metric added: **Extremes**
| [v3.1.2]      | Technical update
| [v3.1.1]      | Technical and documentation update
| [v3.1]        | New metric added: **Precipitation Benchmarking -- distribution bimodality**
| [v3.0.2]      | Minor patch and more documentation added
| [v3.0.1]      | Minor technical patch                 
| [v3.0.0]      | New metric added: **Cloud feedback metric** by @mzelinka. [**xCDAT**](https://xcdat.readthedocs.io/en/latest/) implemented for mean climate metrics

<details>

  <summary>Click here for older versions</summary>

| <div style="width:300%">[Versions]</div> | Update summary   |
| ------------- | ------------------------------------- |
| [v2.5.1]      | Technical update
| [v2.5.0]      | New metric added: **Precipitation Benchmarking -- distribution**. Graphics updated
| [v2.4.0]      | New metric added: **AMO** in variability modes
| [v2.3.2]      | CMEC interface updates
| [v2.3.1]      | Technical update
| [v2.3]        | New graphics using [archived PMP results](https://github.com/PCMDI/pcmdi_metrics_results_archive)
| [v2.2.2]      | Technical update
| [v2.2.1]      | Minor update
| [v2.2]        | New metric implemented: **precipitation variability across time scale**
| [v2.1.2]      | Minor update
| [v2.1.1]      | Simplified dependent libraries and CI process
| [v2.1.0]      | [**CMEC**](https://cmec.llnl.gov/) driver interfaced added.
| [v2.0]        | New capabilities: **ENSO** metrics, demos, and documentations.
| [v1.2]        | Tied to CDAT 8.0. Extensive regression testing added. New metrics: **Diurnal cycle and intermittency of precipitation**, sample **monsoon** metrics.
| [v1.1.2]      | Now managed through Anaconda, and tied to UV-CDAT 2.10.  Weights on bias statistic added. Extensive provenance information incorporated into json files.
| [v1.1]        | First public release, emphasizing **climatological statistics**, with development branches for ENSO and regional monsoon precipitation indices
| [v1.0]        | Prototype version of the PMP

</details>

[Versions]: https://github.com/PCMDI/pcmdi_metrics/releases
[v3.9.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.9.1
[v3.9]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.9
[v3.8.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.8.2
[v3.8.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.8.1
[v3.8]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.8
[v3.7.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.7.2
[v3.7.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.7.1
[v3.7]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.7
[v3.6.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.6.1
[v3.6]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.6
[v3.5.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.5.2
[v3.5.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.5.1
[v3.5]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.5
[v3.4.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.4.1
[v3.4]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.4
[v3.3.4]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.3.4
[v3.3.3]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.3.3
[v3.3.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.3.2
[v3.3.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.3.1
[v3.3]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.3
[v3.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.2
[v3.1.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.1.2
[v3.1.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.1.1
[v3.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.1
[v3.0.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.0.2
[v3.0.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.0.1
[v3.0.0]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v3.0.0
[v2.5.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.5.1
[v2.5.0]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.5.0
[v2.4.0]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.4.0
[v2.3.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.3.2
[v2.3.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.3.1
[v2.3]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.3
[v2.2.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.2.2
[v2.2.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.2.1
[v2.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.2
[v2.1.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.1.2
[v2.1.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.1.1
[v2.1.0]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.1.0
[v2.0]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v2.0
[v1.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v1.2
[v1.1.2]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/1.1.2
[v1.1]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v1.1
[v1.0]: https://github.com/PCMDI/pcmdi_metrics/releases/tag/v1.0

Current Core Development Team
-----------------------------
* [Jiwoo Lee](https://people.llnl.gov/lee1043) ([LLNL](https://www.llnl.gov/), PMP Lead)
* [Kristin Chang](https://people.llnl.gov/chang61) ([LLNL](https://www.llnl.gov/))
* [Peter Gleckler](https://pcmdi.llnl.gov/staff/gleckler/) ([LLNL](https://www.llnl.gov/))
* [Paul Ullrich](https://people.llnl.gov/ullrich4) ([LLNL](https://www.llnl.gov/), [PCMDI](https://pcmdi.llnl.gov/) Project PI)
* [Shixuan Zhang](https://www.pnnl.gov/science/staff/staff_info.asp?staff_num=9376) ([PNNL](https://www.pnnl.gov/))

All Contributors
----------------

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://sites.google.com/view/jiwoolee"><img src="https://avatars.githubusercontent.com/u/17091564?v=4?s=100" width="100px;" alt="Jiwoo Lee"/><br /><sub><b>Jiwoo Lee</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=lee1043" title="Code">💻</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=lee1043" title="Documentation">📖</a> <a href="https://github.com/PCMDI/pcmdi_metrics/pulls?q=is%3Apr+reviewed-by%3Alee1043" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=lee1043" title="Tests">⚠️</a> <a href="#tutorial-lee1043" title="Tutorials">✅</a> <a href="#research-lee1043" title="Research">🔬</a> <a href="#ideas-lee1043" title="Ideas, Planning, & Feedback">🤔</a> <a href="#infra-lee1043" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/gleckler1"><img src="https://avatars.githubusercontent.com/u/4553389?v=4?s=100" width="100px;" alt="Peter Gleckler"/><br /><sub><b>Peter Gleckler</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=gleckler1" title="Code">💻</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=gleckler1" title="Documentation">📖</a> <a href="#research-gleckler1" title="Research">🔬</a> <a href="https://github.com/PCMDI/pcmdi_metrics/pulls?q=is%3Apr+reviewed-by%3Agleckler1" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=gleckler1" title="Tests">⚠️</a> <a href="#data-gleckler1" title="Data">🔣</a> <a href="#ideas-gleckler1" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://kristinchang.github.io/portfolio/"><img src="https://avatars.githubusercontent.com/u/143142064?v=4?s=100" width="100px;" alt="Kristin Chang"/><br /><sub><b>Kristin Chang</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=kristinchang3" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/acordonez"><img src="https://avatars.githubusercontent.com/u/18147700?v=4?s=100" width="100px;" alt="Ana Ordonez"/><br /><sub><b>Ana Ordonez</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=acordonez" title="Code">💻</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=acordonez" title="Documentation">📖</a> <a href="https://github.com/PCMDI/pcmdi_metrics/pulls?q=is%3Apr+reviewed-by%3Aacordonez" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=acordonez" title="Tests">⚠️</a> <a href="#tutorial-acordonez" title="Tutorials">✅</a> <a href="#infra-acordonez" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/msahn"><img src="https://avatars.githubusercontent.com/u/46369397?v=4?s=100" width="100px;" alt="Min-Seop Ahn"/><br /><sub><b>Min-Seop Ahn</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=msahn" title="Code">💻</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=msahn" title="Documentation">📖</a> <a href="https://github.com/PCMDI/pcmdi_metrics/pulls?q=is%3Apr+reviewed-by%3Amsahn" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=msahn" title="Tests">⚠️</a> <a href="#tutorial-msahn" title="Tutorials">✅</a> <a href="#research-msahn" title="Research">🔬</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://climate.ucdavis.edu/"><img src="https://avatars.githubusercontent.com/u/5330916?v=4?s=100" width="100px;" alt="Paul Ullrich"/><br /><sub><b>Paul Ullrich</b></sub></a><br /><a href="#ideas-paullric" title="Ideas, Planning, & Feedback">🤔</a> <a href="#research-paullric" title="Research">🔬</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/doutriaux1"><img src="https://avatars.githubusercontent.com/u/2781425?v=4?s=100" width="100px;" alt="Charles Doutriaux"/><br /><sub><b>Charles Doutriaux</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=doutriaux1" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/taylor13"><img src="https://avatars.githubusercontent.com/u/4993439?v=4?s=100" width="100px;" alt="Karl Taylor"/><br /><sub><b>Karl Taylor</b></sub></a><br /><a href="#research-taylor13" title="Research">🔬</a> <a href="#ideas-taylor13" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/durack1"><img src="https://avatars.githubusercontent.com/u/3229632?v=4?s=100" width="100px;" alt="Paul J. Durack"/><br /><sub><b>Paul J. Durack</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=durack1" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://mzelinka.github.io/"><img src="https://avatars.githubusercontent.com/u/11380489?v=4?s=100" width="100px;" alt="Mark Zelinka"/><br /><sub><b>Mark Zelinka</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=mzelinka" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/bonfils2"><img src="https://avatars.githubusercontent.com/u/3536584?v=4?s=100" width="100px;" alt="Celine Bonfils"/><br /><sub><b>Celine Bonfils</b></sub></a><br /><a href="#research-bonfils2" title="Research">🔬</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://pcmdi.llnl.gov/staff/covey/"><img src="https://pcmdi.llnl.gov/staff/covey/curt.jpg?s=100" width="100px;" alt="Curtis C. Covey"/><br /><sub><b>Curtis C. Covey</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=" title="Code">💻</a> <a href="#research" title="Research">🔬</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/zshaheen"><img src="https://avatars.githubusercontent.com/u/4239938?v=4?s=100" width="100px;" alt="Zeshawn Shaheen"/><br /><sub><b>Zeshawn Shaheen</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=zshaheen" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/muryanto1"><img src="https://avatars.githubusercontent.com/u/35277663?v=4?s=100" width="100px;" alt="Lina Muryanto"/><br /><sub><b>Lina Muryanto</b></sub></a><br /><a href="#infra-muryanto1" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/tomvothecoder"><img src="https://avatars.githubusercontent.com/u/25624127?v=4?s=100" width="100px;" alt="Tom Vo"/><br /><sub><b>Tom Vo</b></sub></a><br /><a href="#infra-tomvothecoder" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/jasonb5"><img src="https://avatars.githubusercontent.com/u/2191036?v=4?s=100" width="100px;" alt="Jason Boutte"/><br /><sub><b>Jason Boutte</b></sub></a><br /><a href="#infra-jasonb5" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/painter1"><img src="https://avatars.githubusercontent.com/u/2799665?v=4?s=100" width="100px;" alt="Jeffrey Painter"/><br /><sub><b>Jeffrey Painter</b></sub></a><br /><a href="#data-painter1" title="Data">🔣</a> <a href="#infra-painter1" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=painter1" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/pochedls"><img src="https://avatars.githubusercontent.com/u/3698109?v=4?s=100" width="100px;" alt="Stephen Po-Chedley"/><br /><sub><b>Stephen Po-Chedley</b></sub></a><br /><a href="#data-pochedls" title="Data">🔣</a> <a href="#infra-pochedls" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://xylar.github.io/"><img src="https://avatars.githubusercontent.com/u/4179064?v=4?s=100" width="100px;" alt="Xylar Asay-Davis"/><br /><sub><b>Xylar Asay-Davis</b></sub></a><br /><a href="#infra-xylar" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.gfdl.noaa.gov/john-krasting-homepage"><img src="https://avatars.githubusercontent.com/u/6594675?v=4?s=100" width="100px;" alt="John Krasting"/><br /><sub><b>John Krasting</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=jkrasting" title="Code">💻</a> <a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=jkrasting" title="Tests">⚠️</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.cgd.ucar.edu/staff/apgrass/"><img src="https://avatars.githubusercontent.com/u/16008440?v=4?s=100" width="100px;" alt="Angeline G Pendergrass"/><br /><sub><b>Angeline G Pendergrass</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=apendergrass" title="Code">💻</a> <a href="#research-apendergrass" title="Research">🔬</a> <a href="#ideas-apendergrass" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/mfwehner"><img src="https://avatars.githubusercontent.com/u/10789148?v=4?s=100" width="100px;" alt="Michael Wehner"/><br /><sub><b>Michael Wehner</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=mfwehner" title="Code">💻</a> <a href="#research-mfwehner" title="Research">🔬</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://sites.google.com/uw.edu/kimresearchgroup"><img src="https://scholar.googleusercontent.com/citations?view_op=view_photo&user=3xLjsIsAAAAJ&citpid=3?s=100" width="100px;" alt="Daehyun Kim"/><br /><sub><b>Daehyun Kim</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=" title="Code">💻</a> <a href="#research" title="Research">🔬</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/bosup"><img src="https://avatars.githubusercontent.com/u/130708142?v=4?s=100" width="100px;" alt="Bo Dong"/><br /><sub><b>Bo Dong</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=bosup" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/zhangshixuan1987"><img src="https://avatars.githubusercontent.com/u/33647254?v=4?s=100" width="100px;" alt="Shixuan Zhang"/><br /><sub><b>Shixuan Zhang</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=zhangshixuan1987" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/ajonko"><img src="https://avatars.githubusercontent.com/u/13386754?v=4?s=100" width="100px;" alt="Alex Jonko"/><br /><sub><b>Alex Jonko</b></sub></a><br /><a href="https://github.com/PCMDI/pcmdi_metrics/commits?author=ajonko" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification.
