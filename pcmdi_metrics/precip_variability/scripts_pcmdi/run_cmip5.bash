
mip='cmip5'
exp='historical'
var='pr'
frq='3hr'
ver='v20210123'

maxjob=15

i=0
for model in `ls /p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/$ver/$mip/$exp/atmos/$frq/$var/`
do
  i=$(($i+1))
  echo $i $model
  nohup python -u ../variability_across_timescales_PS_driver.py -p ../param/variability_across_timescales_PS_${frq}_params_${mip}.py --mod $model  > ./log/log_PS_${frq}_$model &
  echo 'run'
  if [ $(($i%$maxjob)) -eq 0 ]; then
    echo 'wait'
    wait
  fi
done

