import os
import subprocess
import time


def parallel_submitter(cmd_list, log_dir='./logs', logfilename_list=None, num_workers=None):
    """
    Run subprocesses in parallel

    Import (after installing PMP):
    >> from pcmdi_metrics.misc.scripts import parallel_submitter

    Inputs:

    - cmd_list: python list of command lines, e.g.,
     ['python abc.py -p ../../test_param.py -m model1',
      'python abc.py -p ../../test_param.py -m model2',
       :
      'python abc.py -p ../../test_param.py -m model100']

    - log_dir: string for directory path for log files, e.g.,
      '/a/b'
      default = './logs'

    - logfilename_list: python list of pull path of log files, e.g.,
     ['log_model1',
      'log_model2',
       :
      'log_model100']
     In case it was not given, automatically generated as 'log_process_N' (N: process index number)

    - num_workers: integer number that limits how many process to be submitted at one time
       default: 20% of all CPUs of the current computer

    Outputs:
    - processes running in parallel
    - log files in log_dir
    - Each process generates two log files: stdout and stderr
    """

    # ------------------------------------------------------
    # some env. setups...
    # ------------------------------------------------------
    # To avoid below error
    # OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
    os.environ['OPENBLAS_NUM_THREADS'] = '1'

    # Must be done before any CDAT library is called.
    # https://github.com/CDAT/cdat/issues/2213
    if 'UVCDAT_ANONYMOUS_LOG' not in os.environ:
        os.environ['UVCDAT_ANONYMOUS_LOG'] = 'no'
    # ------------------------------------------------------

    os.makedirs(log_dir, exist_ok=True)

    if num_workers is None:
        num_workers = int(os.cpu_count() * 0.2)  # default: use 20% of all available CPUs

    print('Number of employed CPUs for subprocesses:', num_workers)
    print("Parallel process start: %s" % time.ctime())

    processes = list()

    for index, (process, log_file) in enumerate(zip(cmd_list, logfilename_list)):
        print(index, ':', process)

        # LOG FILE
        if logfilename_list is None:
            log_file = os.path.join(log_dir, 'log_process_'+str(index))
        else:
            log_file = os.path.join(log_dir, logfilename_list[index])

        # SUBMIT PROCESS
        with open(log_file+"_stdout.txt", "wb") as out, open(log_file+"_stderr.txt", "wb") as err:
            p = subprocess.Popen(process.split(' '), stdout=out, stderr=err)
            processes.append(p)

        # WAIT FOR NEXT SUBMIT
        if len(processes) == num_workers:
            wait = True
            while wait:
                done, num = check_for_done(processes)
                if done:
                    processes.pop(num)
                    wait = False
                    if index != len(cmd_list)-1:
                        print("Launching next process in cmd_list: %s" % time.ctime())
                else:
                    time.sleep(2)  # set this so the CPU does not go crazy

    # DONE
    print("Parallel process completed: %s" % time.ctime())


def check_for_done(processes):
    for i, p in enumerate(processes):
        if p.poll() is not None:
            return True, i  # subprocess finished
    return False, False  # suprocess not finished


def main():
    cmd_list = ['expr 1 + ' + str(r) for r in range(1, 10)]
    logfilename_list = ['log_' + str(r) for r in range(1, 10)]
    for (process, log_file) in zip(cmd_list, logfilename_list):
        print(process, '\t', log_file)
    num_workers = 2
    parallel_submitter(cmd_list, logfilename_list=logfilename_list, num_workers=num_workers)


if __name__ == "__main__":
    main()
