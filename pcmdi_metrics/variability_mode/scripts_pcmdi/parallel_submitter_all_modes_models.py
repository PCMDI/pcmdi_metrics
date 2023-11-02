import datetime
import glob
import os

from pcmdi_metrics.misc.scripts import parallel_submitter
from pcmdi_metrics.variability_mode.lib import sort_human


def find_latest(path):
    dir_list = [p for p in glob.glob(path + "/v????????")]
    return sorted(dir_list)[-1]

# ---------------------------------------------------------------

mip = "cmip6"
exp = "historical"

datadir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest'
param_dir = "../param"

modes = ["NAM", "SAM", "NAO", "PNA", "NPO", "PDO", "NPGO"]

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())

num_workers = 40
debug = True 

# ---------------------------------------------------------------

cmds_list = list()
logfilename_list = list()

for mode in modes:
    if mode in ["PDO", "NPGO", "AMO"]:
        var = "ts"
        param_file = "myParam_demo_PDO.py"
    else:
        var = "psl"
        param_file = "myParam_demo_NAM.py"

    if mode in ["SAM"]:
        osyear = 1955
    else:
        osyear = 1900

    if mode in ["NPO", "NPGO"]:
        eofn_obs = 2
        eofn_mod = 2
    else:
        eofn_obs = 1
        eofn_mod = 1
    
    datadir_ver = find_latest(datadir)
    datadir_final = os.path.join(datadir_ver, mip, exp, 'atmos', 'mon', var)
    
    xml_list = glob.glob(os.path.join(datadir_final, '*.xml'))
    
    # get list of models
    models_list = sort_human(
        [r.split("/")[-1].split(".")[2] for r in xml_list]
    )
    # remove repeat
    models_list = sort_human(list(dict.fromkeys(models_list)))

    if debug:
        models_list = models_list[0:3]
    
    print(models_list)
    print(len(models_list))
    
    for model in models_list:
        file_list_model = glob.glob(os.path.join(datadir_final, '*.' + model + '.*.xml'))
        runs_list = sort_human(
            [
                r.split("/")[-1].split(".")[3]
                for r in file_list_model
            ]
        )

        if debug:
            runs_list = runs_list[0:1]
    
        print(model, runs_list)

        for run in runs_list:

            cmd_content = [
                'variability_modes_driver.py', 
                '-p', os.path.join(param_dir, param_file), 
                '--variability_mode', mode,
                '--osyear', str(osyear),
                '--eofn_obs', str(eofn_obs),
                '--eofn_mod', str(eofn_mod),
                '--mip', mip, '--exp', exp,
                '--modnames', model,
                '--realization', run,
            ]

            if model != models_list[0] or run != runs_list[0]:
                cmd_content.extend(["--no_plot_obs", "--no_nc_out_obs"])

            if debug:
                cmd_content.append('--debug True')

            cmd = ' '.join(cmd_content)

            log_file = '_'.join(['variability_modes', mode, mip, exp, model, run]) + '.txt'
    
            print(cmd) 
            cmds_list.append(cmd)
            logfilename_list.append(log_file)

# =================================================
# Run subprocesses in parallel
# -------------------------------------------------
# log dir
log_dir = os.path.join(
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2",
    "log",
    "variability_modes",
    mip, exp, case_id)
 
os.makedirs(log_dir, exist_ok=True)

parallel_submitter(
    cmds_list,
    log_dir=log_dir,
    logfilename_list=logfilename_list,
    num_workers=num_workers,
)

