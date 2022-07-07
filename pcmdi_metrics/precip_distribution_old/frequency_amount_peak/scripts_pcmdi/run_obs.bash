
res='90x45'
#res='180x90'
#res='360x180'

nohup python -u ../dist_freq_amount_peak_width_driver.py -p ../param/dist_freq_amount_peak_width_params_CMORPH.py  > ./log/log_CMORPH_$res &
nohup python -u ../dist_freq_amount_peak_width_driver.py -p ../param/dist_freq_amount_peak_width_params_ERA5.py  > ./log/log_ERA5_$res &
nohup python -u ../dist_freq_amount_peak_width_driver.py -p ../param/dist_freq_amount_peak_width_params_GPCP.py  > ./log/log_GPCP_$res &
#nohup python -u ../dist_freq_amount_peak_width_driver.py -p ../param/dist_freq_amount_peak_width_params_IMERG.py  > ./log/log_IMERG_$res &
nohup python -u ../dist_freq_amount_peak_width_driver.py -p ../param/dist_freq_amount_peak_width_params_PERSIANN.py  > ./log/log_PERSIANN_$res &
nohup python -u ../dist_freq_amount_peak_width_driver.py -p ../param/dist_freq_amount_peak_width_params_TRMM.py  > ./log/log_TRMM_$res &

