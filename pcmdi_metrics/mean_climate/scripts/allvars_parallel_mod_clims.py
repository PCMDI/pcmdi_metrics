import datetime
import glob
import os

from pcmdi_metrics.misc.scripts import parallel_submitter


def find_latest(path):
    dir_list = [p for p in glob.glob(path + "/v????????")]
    return sorted(dir_list)[-1]


mip = "cmip5"
# mip = 'cmip6'
# exp = 'historical'
exp = "amip"

data_path = find_latest("/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest")
pathout_base = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/"
    + mip
    + "/"
    + exp
    + "/"
)
start = "1981-01"
end = "2005-12"
numw = 20  # number of workers in parallel processing
verout = datetime.datetime.now().strftime("v%Y%m%d")

vars = [
    "hur",
    "hurs",
    "huss",
    "pr",
    "prw",
    "psl",
    "rlds",
    "rldscs",
    "rlus",
    "rlut",
    "rlutcs",
    "rsds",
    "rsdscs",
    "rsdt",
    "rsus",
    "rsut",
    "rsutcs",
    "sfcWind",
    "ta",
    "tas",
    "tauu",
    "tauv",
    "ts",
    "ua",
    "uas",
    "va",
    "vas",
    "wap",
    "zg",
]

lst1 = []
listlog = []

for var in vars:
    pin = os.path.join(data_path, mip, exp, "atmos", "mon", var)
    lst = sorted(glob.glob(os.path.join(pin, "*r1i1p1*.xml")))

    pathoutdir = os.path.join(pathout_base, verout, var)
    os.makedirs(pathoutdir, exist_ok=True)

    for li in lst:
        print(li.split("."))
        mod = li.split(".")[4]  # model
        rn = li.split(".")[5]  # realization

        outfilename = mip + "." + exp + "." + mod + "." + rn + ".mon." + var + ".nc"
        cmd0 = (
            "pcmdi_compute_climatologies.py --start "
            + start
            + " --end "
            + end
            + " --infile "
        )

        pathout = pathoutdir + "/" + outfilename
        cmd = cmd0 + li + " --outfile " + pathout + " --var " + var

        lst1.append(cmd)
        logf = mod + "." + rn + "." + var
        listlog.append(logf)
        print(logf)

print("Number of jobs starting is ", str(len(lst1)))
parallel_submitter(
    lst1, log_dir="./logs/" + verout, logfilename_list=listlog, num_workers=numw
)
print("done submitting")
