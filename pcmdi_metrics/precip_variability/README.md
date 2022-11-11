# Precipitation variability across timescales

Reference: Ahn, M.-S., P. J. Gleckler, J. Lee, A. G. Pendergrass, and C. Jakob, 2022: Benchmarking Simulated Precipitation Variability Amplitude across Timescales. Journal of Climate. https://doi.org/10.1175/JCLI-D-21-0542.1

Demo: [precipitation variability across timescales](https://github.com/PCMDI/pcmdi_metrics/blob/93c30ce485719ecf6a531a4ee47886160ebb73e4/doc/jupyter/Demo/Demo_7_precip_variability.ipynb)

## Driver code:
- `variability_across_timescales_PS_driver.py`

## Parameter codes:
- `param/`
  - `variability_across_timescales_PS_3hr_params_IMERG.py`
  - `variability_across_timescales_PS_3hr_params_TRMM.py`
  - `variability_across_timescales_PS_3hr_params_CMORPH.py`
  - `variability_across_timescales_PS_3hr_params_cmip5.py`
  - `variability_across_timescales_PS_3hr_params_cmip6.py`

## Run scripts:
- `scripts_pcmdi/`
  - `run_obs.bash`
  - `run_parallel.wait.bash`
