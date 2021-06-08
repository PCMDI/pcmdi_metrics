# Scripts for PCMDI Metrics Package

- `run_pmp.sh`: Compute metrics using single CPU.
  - `PMPdriver_EnsoMetrics.py`
- `run_pmp_parallel.sh`: Compute metrics using multiple CPUs.
  - `parallel_driver.py`
    - `PMPdriver_EnsoMetrics.py`
      - Input parameter file: `my_Param_ENSO.py` or `my_Param_ENSO_obs2obs.py`
- `run_pmp_palallel_obs2obs.sh`: Compute metrics using multiple CPUs but for observation to observation comparison.
  - `parallel_driver.py`
    - `PMPdriver_EnsoMetrics.py`
- `run_pmp_plot_parallel.sh`: Generate dive down plots using multiple CPUs.
  - `parallel_driver_plot.py`
    - `PMPdriver_plot.py`

**NOTE**: *More clean up needed for obs2obs task*
