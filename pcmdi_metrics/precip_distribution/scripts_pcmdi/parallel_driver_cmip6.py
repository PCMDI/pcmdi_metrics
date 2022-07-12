import os
import glob
from pcmdi_metrics.misc.scripts import parallel_submitter

mip='cmip6'
num_cpus = 20

with open('../param/precip_distribution_params_'+mip+'.py') as source_file:
    exec(source_file.read())

file_list = sorted(glob.glob(os.path.join(modpath, "*")))
cmd_list=[]
log_list=[]
for ifl, fl in enumerate(file_list):
    file = fl.split('/')[-1]
    cmd_list.append('python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_'+mip+'.py --mod '+file)
    log_list.append('log_'+file+'_'+str(round(360/res[0]))+'x'+str(round(180/res[1])))
    print(cmd_list[ifl])
print('Number of data: '+str(len(cmd_list)))
    
parallel_submitter(
    cmd_list,
    log_dir='./log',
    logfilename_list=log_list,
    num_workers=num_cpus,
)

