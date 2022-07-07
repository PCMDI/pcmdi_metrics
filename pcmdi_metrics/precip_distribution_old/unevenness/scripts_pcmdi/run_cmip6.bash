mip='cmip6'
exp='historical'
var='pr'
frq='day'
ver='v20210717'

maxjob=15

i=0
for model in `ls /p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/$ver/$mip/$exp/atmos/$frq/$var/`
do
  i=$(($i+1))
  echo $i $model
  nohup python -u ../dist_unevenness_driver.py -p ../param/dist_unevenness_params_${mip}.py --mod $model  > ./log/log_${model}_180x90 &
#   nohup python -u ../dist_unevenness_driver.py -p ../param/dist_unevenness_params_${mip}.py --mod $model  > ./log/log_${model}_90x45 &
  echo $i 'run'
  if [ $(($i%$maxjob)) -eq 0 ]; then
    echo 'wait'
    wait
  fi
done

