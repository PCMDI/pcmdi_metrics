# Precip distribution metrics

Reference: 
Ahn, M.-S., P. A. Ullrich, P. J. Gleckler, J. Lee,  A. C. Ordonez, and A. G. Pendergrass, 2023: Evaluating Precipitation Distributions at Regional Scales: A Benchmarking Framework and Application to CMIP5 and CMIP6. Geoscientific Model Development, 16, 3927–3951, https://doi.org/10.5194/gmd-16-3927-2023.

Ahn, M.-S., P. A. Ullrich, J. Lee, P. J. Gleckler, H.-Y. Ma, C. R. Terai, P. A. Bogenschutz, and A. C. Ordonez, 2023: Bimodality in Simulated Precipitation Frequency Distributions and Its Relationship with Convective Parameterizations, 01 June 2023, PREPRINT (Version 1) available at Research Square, https://doi.org/10.21203/rs.3.rs-2874349/v1. (Under revision)


## Driver code:
- `precip_distribution_driver.py`

## Parameter codes:
- `param/`
  - `precip_distribution_params_IMERG.py`
  - `precip_distribution_params_TRMM.py`
  - `precip_distribution_params_CMORPH.py`
  - `precip_distribution_params_GPCP.py`
  - `precip_distribution_params_PERSIANN.py`
  - `precip_distribution_params_ERA5.py`
  - `precip_distribution_params_cmip5.py`
  - `precip_distribution_params_cmip6.py`

## Run scripts:
- `scripts_pcmdi/`
  - `run_obs.bash`
  - `run_parallel.wait.bash`

## Note
- Input data: daily averaged precipitation
- This code should be run for a reference observation initially as some metrics (e.g., Perkins score) need a reference.
- After completing calculation for a reference observation, this code can work for multiple datasets at once.
- This benchmarking framework provides three tiers of area averaged outputs for i) large scale domain (Tropics and Extratropics with separated land and ocean) commonly used in the PMP , ii) large scale domain with clustered precipitation characteristics (Tropics and Extratropics with separated land and ocean, and separated heavy, moderate, and light precipitation regions), and iii) modified IPCC AR6 regions shown in the reference paper.
