ref='IMERG'
exp='amip'
resn='180x90'
ver='v20220108'

inpath='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/'$ver'/diagnostic_results/precip_distribution'

outpath='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/'$ver

nohup python -u ./calc_perkins.score.py --exp $exp --ref $ref --resn $resn --ver $ver --modpath "$inpath" --results_dir "$outpath" > ./log/log_calc_perkins.score_$resn &

