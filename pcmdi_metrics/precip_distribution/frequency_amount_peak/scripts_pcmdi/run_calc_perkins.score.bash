# ref='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/obs/v20210717/dist_freq.amount_regrid.90x45_TRMM.nc'
# ref='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/obs/v20210717/dist_freq.amount_regrid.180x90_TRMM.nc'
#ref='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/obs/v20210717/dist_freq.amount_regrid.360x180_TRMM.nc'
#ref='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/obs/v20210717/dist_freq.amount_regrid.720x360_TRMM.nc'

# ref='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/obs/v20210717/dist_freq.amount_regrid.90x45_IMERG.nc'
ref='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/obs/v20210717/dist_freq.amount_regrid.180x90_IMERG.nc'
#ref='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/obs/v20210717/dist_freq.amount_regrid.360x180_IMERG.nc'
#ref='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/obs/v20210717/dist_freq.amount_regrid.720x360_IMERG.nc'


# modpath='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/*/historical/v20210717/'
modpath='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/cmip6/historical/v20210717/'
# modpath='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/diagnostic_results/precip_distribution/*/v20210717/'

results_dir='/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/v20210717/'


# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_90x45 &
# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_180x90 &
nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_180x90_rerun &
# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_360x180 &
# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_720x360 &

# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_obs_90x45 &
# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_obs_180x90 &
# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_obs_360x180 &
# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_obs_720x360 &

# nohup python -u ./calc_perkins.score.py --ref $ref --modpath "$modpath" --results_dir $results_dir  > ./log/log_calc_perkins.score_tmp &
