mkdir ./log
nohup python -u parallel_driver_cmip5.py  > ./log/log_parallel.wait_cmip5 &
wait
nohup python -u parallel_driver_cmip6.py  > ./log/log_parallel.wait_cmip6 &
