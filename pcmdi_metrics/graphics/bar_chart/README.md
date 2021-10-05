# Bar Chart for PMP Results

Visualize PMP output in bar chart template is useful for quick checks on statistics.

## Usage

For one season:
```
python bar_chart.py -j 'metrics_results/pr_2.5x2.5_esmf_linear_metrics.json' -s 'djf' -e 'amip' -d 'NHEX' -v 'pr'
```
![plot](./example_plot/pr_amip_bias_1panel_djf_NHEX.png)

For all seasons:
```
python bar_chart.py -j 'metrics_results/pr_2.5x2.5_esmf_linear_metrics.json' -s 'all' -e 'amip' -d 'NHEX' -v 'pr'
```
![plot](./example_plot/pr_amip_bias_5panel_all_NHEX.png)
