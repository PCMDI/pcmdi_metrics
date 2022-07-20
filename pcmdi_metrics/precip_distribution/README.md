# Precip distribution metrics

Reference: Ahn, M.-S., P. A. Ullrich, P. J. Gleckler, J. Lee,  A. C. Ordonez, A. G. Pendergrass, and C. Jakob, 2022: Framework for Benchmarking Simulated Precipitation Distributions at Regional Scales. Geoscientific Model Development (in prep)

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
