*PMP Viewer is currently in the prototype stage.*

Overview
-----------------------------
This tool offers a one-stop summary of PMP visualizations. Multi-model results from CMIP5 and CMIP6 can be viewed for the following metrics (Please refer to the [PCMDI Website](https://pcmdi.llnl.gov/research/metrics/) for more information on each metric.):
* Mean Climate
* Extratropical Modes of Variability
* El Niño-Southern Oscillation (ENSO)

The PMP Viewer API outputs an interactive page with custom filters for easy navigation of available plots generated by the PMP. By clicking or double-clicking column names, users can also sort tables allowing for quick analysis of data from the PCMDI Database Archive.

All images and plots included are readily available on the PCMDI website; however, PMP Viewer provides a quick way to view dive down information. Users can either refer to the CMIP5 and CMIP6 PMP viewer on (coming soon to) the PCMDI website, or use the API to generate their own version. Currently, there is flexibility to customize the MIPs, Experiments, and Metrics included in the HTML summary. Future plans include allowing users to view their own model results alongside selected MIPs.

Example
-----------------------------
The top function in this API is `generate_pmp_output_viewer_multimodel()`. To generate a basic summary page, please use the following: <br>
`from pmp_output_viewer import generate_pmp_output_viewer_multimodel` <br> or,
`from pcmdi_metrics.viewer import generate_pmp_output_viewer_multimodel` after installation of PMP. <br>
`view_pmp_output(mips=['cmip5', 'cmip6'], exps=['historical', 'amip'], metrics=['mean_climate', 'variability_modes', 'enso_metric'])`

Contributors
-----------------------------
* [Kristin Chang](https://people.llnl.gov/chang61) ([LLNL](https://www.llnl.gov/))
* [Jiwoo Lee](https://people.llnl.gov/lee1043) ([LLNL](https://www.llnl.gov/), PMP Lead)
