import datetime
import os
import string

ver = datetime.datetime.now().strftime("v%Y%m%d")

exp = "historical"

mod_name = "GFDL-CM4.r1i1p1f1"

realization = "shit"

modpath = "/export/gleckler1/processing/metrics_package/my_test/mfw_extremes/cmip6.historical.GFDL-CM4.r1i1p1f1.mon.pr_smalldomain.nc"

results_dir = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/daily_extremes/cmip6/"
    + exp
)

try:
    os.mkdir(results_dir + "/" + ver)
except:
    pass

results_dir = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/daily_extremes/cmip6/"
    + exp
    + "/"
    + ver
)
