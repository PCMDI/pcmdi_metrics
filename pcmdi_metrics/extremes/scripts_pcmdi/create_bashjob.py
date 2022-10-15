import datetime
import glob

ver = datetime.datetime.now().strftime("v%Y%m%d")

ver_in = "v20200815"  # 'v20200526'  #'v20200522'   #'v20200511'  #'v20200428'
mip = "cmip6"
exp = "historical"  #'amip'

pin = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/"
    + ver_in
    + "/"
    + mip
    + "/"
    + exp
    + "/atmos/day/pr/*r1i1p1f1*.xml"
)

file_list = glob.glob(pin)

cmd = (
    "nohup python driver_extrema_longrun_pentad.py -p daily_extremes_input_params.py --modpath /p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/"
    + ver_in
    + "/"
    + mip
    + "/"
    + exp
    + "/atmos/day/pr/cmip6.historical.MODEL.day.pr.xml --mod_name "
)


f = open(mip + "_" + exp + "_MFW_jobs_" + ver + ".bash", "w+")

for file_path_name in file_list:
    mod = file_path_name.split(".")[4] + "." + file_path_name.split(".")[5]

    cmd1 = cmd.replace("MODEL", mod)
    cmd2 = cmd1 + " " + mod + " " + " > " + mod + "." + mip + "." + exp + ".log &"
    print(cmd2)
    f.write(cmd2 + "\n")

f.close()
