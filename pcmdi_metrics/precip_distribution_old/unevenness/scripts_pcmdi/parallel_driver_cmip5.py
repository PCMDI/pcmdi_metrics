import os
import glob
from pcmdi_metrics.misc.scripts import parallel_submitter

mip='cmip5'
num_cpus = 20
# num_cpus = 25

with open('../param/dist_unevenness_params_'+mip+'.py') as source_file:
    exec(source_file.read())

file_list = sorted(glob.glob(os.path.join(modpath, "*")))
cmd_list=[]
log_list=[]
for ifl, fl in enumerate(file_list):
    file = fl.split('/')[-1]
    cmd_list.append('python -u ../dist_unevenness_driver.py -p ../param/dist_unevenness_params_'+mip+'.py --mod '+file)
    log_list.append('log_'+file+'_'+str(round(360/res[0]))+'x'+str(round(180/res[1])))
    print(cmd_list[ifl])
print('Number of data: '+str(len(cmd_list)))
    
parallel_submitter(
    cmd_list,
    log_dir='./log',
    logfilename_list=log_list,
    num_workers=num_cpus,
)

