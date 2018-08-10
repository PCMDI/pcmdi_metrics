#!/usr/bin/env python
from __future__ import print_function
from pcmdi_metrics.driver.pmp_parser import PMPParser
import subprocess
import os
import importlib
import sys
import inspect
import tempfile
import cdp
import shlex
import copy
import distutils.spawn
import stat

parser = PMPParser(description='Parallelize a driver over some arguments')
parser.add_argument("--driver", help="driver to prallelize")
parser.add_argument("--bash", help="generate a bash script rather than running in parallel", action="store_true")
parser.use("num_workers")
p = parser.get_parameter()

param_name = parser.view_args().parameters
pth = os.path.dirname(os.path.abspath(param_name))
sys.path.insert(0, pth)
nm = os.path.basename(param_name)[:-3]
parameters = importlib.import_module(nm)


def build(variables, parameters, params=[{}]):
    if len(variables) == 0:
        return params
    var = variables.pop(0)
    values = getattr(parameters, var)
    len_in = len(params)
    count = len(values)
    nparms = len(params)
    while len(params) < count*nparms:
        params += copy.deepcopy(params[:nparms])
    for i in range(len_in):
        for j in range(len(values)):
            params[j*len_in+i][var] = values[j]
    return build(variables, parameters, params)


def build_command_lines(driver, parameters, matrix):
    cmds = []
    for mydict in matrix:
        f, filename = tempfile.mkstemp(suffix=".py", text=True)
        f = open(filename, "w")
        for att in dir(parameters):
            if att[:2] == "__":
                continue
            val = getattr(parameters, att)
            if inspect.ismodule(val) or inspect.isbuiltin(val) or \
               inspect.ismethod(val) or inspect.isfunction(val):
                continue
            if att in ['granularize']:
                continue
            if att in mydict:
                val = mydict[att]
            print(att, "=", repr(val), file=f)
        f.close()
        cmd = "{} -p {}".format(driver, filename)
        if os.path.exists(driver):
            cmd = "{}/bin/python {}".format(sys.prefix, cmd)
        elif distutils.spawn.find_executable(driver) is None:
            raise RuntimeError(
                "cannot find driver: '{}', it does not appear to be an executable on your path either".format(driver))
        cmds.append(cmd)
    return cmds


def run_command(cmd):
    print("Executing:", cmd)
    sp = cmd.split()[-1]
    print(os.path.exists(sp))
    p = subprocess.Popen(shlex.split(cmd))
    p.communicate()


matrix = build(p.granularize, parameters)
cmds = build_command_lines(p.driver, parameters, matrix)
if p.bash:
    bash_filename = os.path.splitext(os.path.basename(p.driver))[0]+"_bash.bash"
    with open(bash_filename, "w") as fout:
        print("#!/usr/bin/env bash", file=fout)
        print("\n".join(cmds), file=fout)
    print("Bash file stored in: {}".format(os.path.abspath(bash_filename)))
    st = os.stat(bash_filename)
    os.chmod(bash_filename, st.st_mode | stat.S_IEXEC)
else:
    cdp.cdp_run.multiprocess(run_command, cmds, num_workers=p.num_workers)
print("Done")
