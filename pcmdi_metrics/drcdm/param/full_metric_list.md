## Full Metric List (10/28)
Default values for "include_metrics" parameter in drcdm/param/param.py
```
['ref_q_tasmax', 'mean_tasmax', 'monthly_mean_tasmax', 'tasmax_q99p9', 'tasmax_q50', 'annual_txx', 'annual_5day_max_tasmax', 'annual_tasmax_ge', 'annual_tasmax_le', 'tmax_days_above_q', 'tmax_days_below_q', 'ref_q_tasmin', 'ref_q_tasmin', 'annual_tnn', 'mean_tasmin', 'monthly_mean_tasmin', 'annual_5day_min_tasmin', 'annual_5day_max_tasmin', 'annual_tasmin_le', 'annual_tasmin_ge', 'first_date_below', 'last_date_below', 'chill_hours', 'growing_season', 'tmin_days_above_q', 'tmin_days_below_q', 'ref_pr_Q', 'total_pr', 'mean_pr', 'monthly_pr', 'annual_pxx', 'annual_pr_ge', 'wettest_5yr_total', 'annual_max_nday_pr', 'annual_cwd', 'annual_cdd', 'annual_JJA_cdd', 'pr_q50', 'pr_q95', 'pr_q99p9', 'pr_days_above_non_zero_q', 'pr_days_above_q', 'pr_sum_above_q', 'mean_tas', 'monthly_mean_tas', 'annual_cooling_deg_days', 'annual_heating_deg_days', 'annual_growing_deg_days'
]

```

---

## Tasmax Metrics

| Metric Name         | Description |
|---------------------|-------------|
| ref_q_tasmax        | Maximum temperature $Q^{\textrm{th}}$ quantile within the reference dataset. Used to calculate tmax_days_above_q and tmax_days_below_q. |
| mean_tasmax         | Annual and seasonal (DJF, MAM, JJA, SON) mean daily maximum temperature. |
| monthly_mean_tasmax | Monthly mean daily maximum temperature. |
| q99p9_tasmax        | 99.9th percentile of daily maximum temperature. |
| median_tasmax       | Median of daily maximum temperature. |
| annual_txx          | Annual maximum value of daily maximum temperature. |
| 5day_max_tasmax     | Maximum 5-day running mean of daily maximum temperature. |
| annual_tasmax_ge    | Perecent of days per year with daily maximum temperature greater than or equal to a threshold. |
| annual_tasmax_le    | Percent of days per year with daily maximum temperature less than or equal to a threshold. |
| tmax_days_above_q | Percent of days per year with daily maximum temperature above the reference quantile threshold. |
| tmax_days_below_q | Perecent of days per year with daily maximum temperature below the reference quantile threshold. |

---

## Tasmin Metrics

| Metric Name         | Description |
|---------------------|-------------|
| ref_q_tasmin        | Minimum temperature $Q^{\textrm{th}}$ quantile within the reference dataset. Used to calculate tmin_days_above_q and tmin_days_below_q. |
| annual_tnn          | Annual minimum value of daily minimum temperature. |
| annual_mean_tasmin  | Annual mean daily minimum temperature. |
| monthly_mean_tasmin | Monthly mean daily minimum temperature. |
| 5day_min_tasmin     | Minimum 5-day running mean of daily minimum temperature. |
| 5day_max_tasmin     | Maximum 5-day running mean of daily minimum temperature. |
| annual_tasmin_le    | Number of days per year with daily minimum temperature less than or equal to a threshold. |
| annual_tasmin_ge    | Number of days per year with daily minimum temperature greater than or equal to a threshold. |
| first_date_below    | Number of days after August 1st when daily minimum temperature falls below a threshold. |
| last_date_below     | Number of days prior to August 1st when daily minimum temperature falls below a threshold. |
| chill_hours         | Total number of hours per season/year with temperature below a chill threshold. Calculated using Baldocci and Wong (2008) method |
| growing_season      | Number of days between the last occurrence of a minimum temperature at or below threshold in the spring and the first occurrence of a minimum temperature at or below threshold in the fall|
| tmin_days_above_q | Number of days per year with daily minimum temperature above the reference quantile threshold. |
| tmin_days_below_q | Number of days per year with daily minimum temperature below the reference quantile threshold. |

---

## Precipitation Metrics
Days in which less that 1mm of precipitation fell are by default set to 0mm of precipitation.  

| Metric Name                | Description |
|----------------------------|-------------|
| ref_pr_Q                   | Precipitation $Q^{\textrm{th}}$ quantile within the reference dataset. Used to calculate pr_days_above_q and related metrics. |
| annual_mean_pr             | Annual mean daily precipitation. |
| monthly_pr                 | Monthly total precipitation. |
| annual_pxx                 | Annual maximum daily precipitation. |
| annual_pr                  | Annual total precipitation. |
| annual_days_pr_ge_thresh   | Number of days per year with precipitation greater than or equal to a threshold. |
| wettest_5year_total        | Wettest consecutive 5-year total precipitation. |
| annual_nday_pr             | Maximum precipitation sum over n consecutive days (n-day precipitation extreme). |
| annual_cwd                 | Annual maximum number of consecutive wet days. |
| annual_cdd                 | Annual maximum number of consecutive dry days. |
| annual_JJA_cdd             | Maximum number of consecutive dry days in JJA (summer). |
| median_pr                  | Median daily precipitation. |
| pr_q95                     | 95th percentile of daily precipitation. |
| pr_q99p9                   | 99.9th percentile of daily precipitation. |
| pr_days_above_non-zero_q | Number of days per year with precipitation above a quantile threshold. Quantile threshold calculated by excluding days with zero precipitation. |
| pr_days_above_q          | Number of days per year with precipitation above the reference quantile threshold. |
| pr_sum_above_q           | Total precipitation sum above the reference quantile threshold. |

---

## Mean Temperature Metrics
These metrics are computed when tasmax and tasmin are provided and the compute_tasmean parameter is set to True.

| Metric Name                | Description |
|----------------------------|-------------|
| mean_tasmean               | Annual and seasonal mean daily mean temperature. |
| monthly_mean_tas           | Monthly mean daily mean temperature. |
| annual_cooling_deg_days    | Annual cooling degree days (sum of degrees above a base temperature). |
| annual_heating_deg_days    | Annual heating degree days (sum of degrees below a base temperature). |
| growing_deg_days           | Growing degree days, used to estimate plant development rates. |

---

## Other Variable Metrics
Default metrics when the provided variable is not "tasmax", "tasmin", "pr", or "tas".

| Metric Name                | Description |
|----------------------------|-------------|
| mean                       | Annual and seasonal mean|
| monthly_mean               | Monthly mean|
| annual_max                 | Annual maximum value|
