import glob, os
import datetime

var = "tas"
exp = "historical"
mip = "cmip6"
verin = "v20201226"
start = "1980-01"
end = "2005-12"

#################

pin = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/"
    + verin
    + "/"
    + mip
    + "/"
    + exp
    + "/atmos/mon/"
    + var
    + "/"
)

verout = datetime.datetime.now().strftime("v%Y%m%d")

lst = glob.glob(pin + "*r1i1p1f1*.xml")

pathout_base = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/"
    + mip
    + "/"
    + exp
    + "/"
)

try:
    os.mkdir(pathout_base + verout)
except:
    pass
try:
    os.mkdir(pathout_base + verout + "/" + var)
except:
    pass

# pathout = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/' + mip + '/' + exp + '/' + verout + '/' + var + '/'
pathout = pathout_base + verout + "/" + var

cmd0 = (
    "python ./clim_calc_driver.py -p clim_calc_cmip_inparam.py --start "
    + start
    + " --end "
    + end
    + " --infile "
)

lst1 = []
for l in lst:
    cmd = (
        "nohup "
        + cmd0
        + l
        + " --outpath "
        + pathout
        + " --var "
        + var
        + " > log."
        + mip
        + "."
        + exp
        + "."
        + var
        + "."
        + verin
        + ".txt"
        + " & \n"
    )
    print(cmd)
    lst1.append(cmd)

fout = open(var + "." + mip + "." + exp + "." + verin + "." + verout + ".bash", "w+")
fout.writelines(lst1)
fout.close()
