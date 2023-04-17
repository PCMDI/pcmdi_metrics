mkdir -p ./log
nohup python -u parallel_driver_cmip.py  -p ../param/precip_distribution_params_cmip5.py > ./log/log_parallel.wait_cmip5 &
wait
nohup python -u parallel_driver_cmip.py -p ../param/precip_distribution_params_cmip6.py  > ./log/log_parallel.wait_cmip6 &
