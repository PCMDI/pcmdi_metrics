## Default Threshold Dictionary
If you don't set custom_thresholds in drcdm/param/param.py, these will be the default values.

```
default_thresholds = {  # accepted units - degF, degC, degK (temp), mm, inches (precip)
    "tasmin_ge": {"values": [70, 75, 80, 85, 90], "units": "degF"},
    "tasmin_le": {"values": [0, 32], "units": "degF"},
    "tasmax_ge": {"values": [86, 90, 95, 100, 105, 110, 115], "units": "degF"},
    "monthly_tasmax_ge": {"values": [95], "units": "degF"},
    "monthly_tasmin_le": {"values": [32], "units": "degF"},
    "tasmax_le": {"values": [28, 32, 41], "units": "degF"},
    "growing_season": {"values": [32], "units": "degF"},
    "pr_ge": {"values": [0, 1, 2, 3, 4], "units": "inches"},
    "pr_ge_quant": {"values": [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99], "units": "%"},
    "tasmax_ge_quant": {"values": [99], "units": "%"},
    "tasmax_le_quant": {"values": [1],  "units": "%"},
    "tasmin_ge_quant": {"values": [99], "units": "%"},
    "tasmin_le_quant": {"values": [1],  "units": "%"},
}
```
## Descriptions
| Threshold Name | Description |
-----------------|-------------
| tasmin_ge | % of days per year with daily minimum temperature >= $X{^\circ}$ |
| tasmin_le | % of days per year with daily minimum temperature <= $X{^\circ}$ |
| tasmax_ge | % of days per year with daily maximum temperature >= $X{^\circ}$ |
| tasmax_ge | % of days per year with daily maximum temperature <= $X{^\circ}$ |
|growing_season | Number of days between the last occurrence of a minimum temperature at or below $X{^\circ}$ in the spring and the first occurrence of a minimum temperature at or below $X{^\circ}$ in the fall |
| pr_ge | % of days per year with precipitation >= (X unit) |
| pr_ge_quant | % of days per year with precipitation >= the $Q^{\textrm{th}}$ quantile in the reference (or model) dataset|
| tasmax_ge_quant | % of days per year with maximum temperature >= the $Q^{\textrm{th}}$ quantile in the reference (or model) dataset|
| tasmax_le_quant | % of days per year with maximum temperature <= the $Q^{\textrm{th}}$ quantile in the reference (or model) dataset|
| tasmin_ge_quant | % of days per year with minimum temperature >= the $Q^{\textrm{th}}$ quantile in the reference (or model) dataset|
| tasmin_le_quant | % of days per year with minimum temperature <= the $Q^{\textrm{th}}$ quantile in the reference (or model) dataset|
