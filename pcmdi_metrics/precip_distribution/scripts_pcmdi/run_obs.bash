#res='90x45'
res='180x90'
#res='360x180'

mkdir ./log
# nohup python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_CMORPH.py  > ./log/log_CMORPH_$res &
# nohup python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_ERA5.py  > ./log/log_ERA5_$res &
# nohup python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_GPCP.py  > ./log/log_GPCP_$res &
nohup python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_IMERG.py  > ./log/log_IMERG_$res &
# nohup python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_PERSIANN.py  > ./log/log_PERSIANN_$res &
# nohup python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_TRMM.py  > ./log/log_TRMM_$res &

