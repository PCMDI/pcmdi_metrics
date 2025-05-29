# Decision Relevant Climate Data Metrics

# How to test:
Create a conda environment with pcmdi_metrics and xclim
In the PMP root directory use:
`pip install .`

Edit the metrics output path in pcmdi_metrics/drcdm/param/drcdm_param.py to be a location at which you have write permission.

To launch a run with the demo parameter file use:
`drcdm_driver.py -p pcmdi_metrics/drcdm/param/drcdm_param.py`

# Parameter File 
Parameters that must be set 
- Var