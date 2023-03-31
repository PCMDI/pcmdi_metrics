# res='90x45'
res='180x90'
# res='360x180'

# data='IMERG CMORPH ERA5 GPCP PERSIANN TRMM CFSR ERA-Interim JRA-55 MERRA MERRA2'
data='IMERG'
# data='CMORPH ERA5 GPCP PERSIANN TRMM CFSR ERA-Interim JRA-55 MERRA MERRA2'
# data='CMORPH ERA5 GPCP PERSIANN TRMM'
# data='CFSR ERA-Interim JRA-55 MERRA MERRA2'
# data='ERA-Interim JRA-55 MERRA MERRA2'
# data='ERA-Interim ERA5 TRMM'
# data='ERA-Interim PERSIANN'
# data='TRMM ERA-Interim PERSIANN'
# data='IMERG CMORPH ERA5 GPCP PERSIANN TRMM CFSR  JRA-55  MERRA2'
# data='ERA5 ERA-Interim'
# data='CFSR JRA-55 MERRA2'
# data='MERRA'
# data='TRMM'
# data='ERA-Interim'
# data='PERSIANN'


mkdir ./log
for idat in $data
do
  echo $idat
  nohup python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_$idat.py  > ./log/log_${idat}_$res &
done
