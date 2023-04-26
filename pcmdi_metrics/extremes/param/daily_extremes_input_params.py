import datetime
import os

ver = datetime.datetime.now().strftime("v%Y%m%d")

exp = "historical"
mod_name = "randint"
realization = "r1i1p1f1"
modpath = "/home/ordonez4/git/pcmdi_metrics/pcmdi_metrics/extremes/test_data/lowres_randint_1980-1999.nc"

results_dir = os.path.join(
    ".",
    exp,
)

try:
    os.makedirs(results_dir + "/" + ver, exist_ok=True)
except Exception:
    pass

