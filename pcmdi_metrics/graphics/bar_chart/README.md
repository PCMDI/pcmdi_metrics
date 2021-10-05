# Usage

For one season:
```
python bar_chart_bias.py -j '/Users/lee1043/Documents/Research/PMP/metrics_results/cmip5clims_metrics_package-historical/v1.1/pr_2.5x2.5_esmf_linear_metrics.json' -s 'djf' -e 'amip' -d 'NHEX' -v 'pr'
```
![plot](./example_plot/pr_amip_bias_1panel_djf_NHEX.png)

For all seasons:
```
python bar_chart_bias.py -j '/Users/lee1043/Documents/Research/PMP/metrics_results/cmip5clims_metrics_package-historical/v1.1/pr_2.5x2.5_esmf_linear_metrics.json' -s 'all' -e 'amip' -d 'NHEX' -v 'pr'
```
![plot](./example_plot/pr_amip_bias_5panel_all_NHEX.png)
