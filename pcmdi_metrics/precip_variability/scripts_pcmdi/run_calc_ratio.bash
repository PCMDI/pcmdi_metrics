ref='/work/ahn6/pr/variability_across_timescales/power_spectrum/v20210123_test/metrics_results/precip_variability/obs/v20210702/PS_pr.3hr_regrid.180x90_area.freq.mean_TRMM.json'
modpath='/work/ahn6/pr/variability_across_timescales/power_spectrum/v20210123_test/metrics_results/precip_variability/cmip6/historical/v20210702'
results_dir='/work/ahn6/pr/variability_across_timescales/power_spectrum/v20210123_test/metrics_results/precip_variability/cmip6/historical/v20210702/ratio'

nohup python -u ./calc_ratio.py --ref $ref --modpath $modpath --results_dir $results_dir  > ./log/log_calc_ratio &

