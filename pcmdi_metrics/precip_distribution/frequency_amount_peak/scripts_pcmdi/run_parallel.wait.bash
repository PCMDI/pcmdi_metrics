#nohup ./run_cmip5.bash  > ./log/log_parallel.wait_cmip5 &
#nohup ./run_cmip6.bash  > ./log/log_parallel.wait_cmip6 &

#nohup python -u parallel_driver_cmip5.py  > ./log/log_parallel.wait_cmip5 &
#wait
nohup python -u parallel_driver_cmip6.py  > ./log/log_parallel.wait_cmip6 &
