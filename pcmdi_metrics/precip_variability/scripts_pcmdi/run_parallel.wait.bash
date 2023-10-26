mkdir ./log
nohup python -u parallel_driver_cmip.py -p ../param/variability_across_timescales_PS_3hr_params_cmip5.py > ./log/log_parallel.wait_cmip5 &
wait
nohup python -u parallel_driver_cmip.py -p ../param/variability_across_timescales_PS_3hr_params_cmip6.py > ./log/log_parallel.wait_cmip6 &

# nohup python -u parallel_driver_cmip.py -p ../param/variability_across_timescales_PS_3hr_params_cmip6.py --mod 'EC-Earth3' > ./log/log_parallel.wait_cmip6 &
