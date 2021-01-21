from __future__ import print_function
from subprocess import Popen

import os
import time


def parallel_submitter(cmd_list, log_dir, logfilename_list, num_workers=3):
    """
    Run subprocesses in parallel

    Inputs:
    
    - cmd_list: python list of command lines, e.g.,
     ['python abc.py -p ../../test_param.py -m model1',
      'python abc.py -p ../../test_param.py -m model2',
       :
      'python abc.py -p ../../test_param.py -m model100']

    - log_dir: string for directory path for log files, e.g., 
      '/a/b'
     
    - logfilename_list: python list of pull path of log files, e.g., 
     ['log_model1',
      'log_model2',
       :
      'log_model100']
     
    - num_workers: integer number that limits how many process to be submitted at one time
       default = 3

    Outputs:

    - processes running in parallel
    - log files in log_dir
    - Each process generates two log files: stdout and stderr
    
    """

    os.makedirs(log_dir, exist_ok=True)
    
    print("Start : %s" % time.ctime())
    
    # submit tasks and wait for subset of tasks to complete
    procs_list = []
    for p, cmd in enumerate(cmds_list):
        print(p, ':', cmd)
        log_file = os.path.join(log_dir, logfilename_list[p])
        with open(log_file+"_stdout.txt", "wb") as out, open(log_file+"_stderr.txt", "wb") as err:
            procs_list.append(Popen(cmd.split(' '), stdout=out, stderr=err))
        if ((p > 0 and p % num_workers == 0) or (p == len(cmds_list)-1)):
            print('wait...')
            for proc in procs_list:
                proc.wait()
            print("Tasks end : %s" % time.ctime())
            procs_list = []
    
    # tasks done
    print("End : %s" % time.ctime())
    print("Parallel process completed") 
