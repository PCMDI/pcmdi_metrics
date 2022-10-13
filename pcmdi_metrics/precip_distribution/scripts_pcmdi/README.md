# Usage

Adjust `ncpu` in `parallel_driver_cmip.py`

## CMIP5
python -u parallel_driver_cmip.py  -p ../param/precip_distribution_params_cmip5.py > ./log/log_parallel.wait_cmip5 &

## CMIP6
python -u parallel_driver_cmip.py -p ../param/precip_distribution_params_cmip6.py  > ./log/log_parallel.wait_cmip6 &

## Running for one model with `--mod` option
e.g.) python -u parallel_driver_cmip.py  -p ../param/precip_distribution_params_cmip5.py --mod ACCESS1-0 > ./log/log_parallel.wait_cmip5 &
