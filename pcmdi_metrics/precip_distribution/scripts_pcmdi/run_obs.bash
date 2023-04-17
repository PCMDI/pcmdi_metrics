# res='90x45'
res='180x90'
# res='360x180'

# data='IMERG CMORPH ERA5 GPCP PERSIANN TRMM CFSR ERA-Interim JRA-55 MERRA MERRA2'
data='IMERG'
# data='CMORPH ERA5 GPCP PERSIANN TRMM CFSR ERA-Interim JRA-55 MERRA MERRA2'


mkdir -p ./log
for idat in $data
do
  echo $idat
  nohup python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_$idat.py  > ./log/log_${idat}_$res &
done
