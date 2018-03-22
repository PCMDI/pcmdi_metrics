#!/usr/bin/env python
from __future__ import print_function
import argparse
import time
import subprocess
import os
import sys
import shlex


loc = time.localtime()
today = "%s.%s.%s" % (loc.tm_year, loc.tm_mon, loc.tm_mday)

P = argparse.ArgumentParser(
    description='Merge many branches into a conda env',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

c = P.add_argument_group('CONDA')
c.add_argument("-e", "--env", default=today, help="conda env to install into")
c.add_argument("-x", "--extra", default="", help="extra packages and channels you need")
c.add_argument(
    "-M",
    "--no-mesa",
    default=False,
    action="store_true",
    help="turn on/off mesa")
c.add_argument(
    "-n",
    "--no-nightly",
    default=False,
    action="store_true",
    help="turn on/off mesa")
b = P.add_argument_group('Repositories')
b.add_argument(
    "-m",
    "--metrics",
    default=["master"],
    nargs="*",
    help="metrics branches to merge in")
b.add_argument("-r", "--repo", default="PCMDI/pcmdi_metrics",
               help="metrics repo to use")
b.add_argument(
    "-v",
    "--vcs",
    default=["master"],
    nargs="*",
    help="vcs branches to merge")
b.add_argument(
    "-c",
    "--cdms",
    default=["master"],
    nargs="*",
    help="cdms branches to merge")
loc = P.add_argument_group('Local Setup')
loc.add_argument("-g", "--git", default=os.path.expanduser("~/git"),
                 help="top directory where you will clone your git repos")

args = P.parse_args(sys.argv[1:])

sp = args.repo.split("/")
metrics_repo = sp[0]
metrics_name = "/".join(sp[1:])


def execute_cmd(cmd, path=os.getcwd()):
    print(("Executing: %s in: %s" % (cmd, path)))
    p = subprocess.Popen(shlex.split(cmd), cwd=path)
    o, e = p.communicate()
    return o, e


def merge_branches(repo_pth, branches):
    execute_cmd("git checkout master", path=repo_pth)
    execute_cmd("git reset --hard origin/master", path=repo_pth)
    execute_cmd("git pull", path=repo_pth)
    for b in branches:
        execute_cmd("git merge --no-commit origin/%s" % b, path=repo_pth)


# Make sure we yank conda
execute_cmd("conda clean --lock")
execute_cmd("conda remove -n %s -y --all" % args.env)

if args.no_mesa:
    pname = ""
else:
    pname = "-nox"

if args.no_nightly:
    nightly = ""
else:
    nightly = "-c uvcdat/label/nightly"
# Create conda env
execute_cmd(
    "conda create -y -n %s %s -c uvcdat %s ipython output_viewer eztemplate vcsaddons%s cdms2 vcs%s hdf5=1.8.16 " %
    (args.env, nightly, args.extra, pname, pname))

# Setup GIT
if not os.path.exists(args.git):
    os.makedirs(args.git)

# Loop through vcs branches
execute_cmd("git clone git://github.com/UV-CDAT/vcs", path=args.git)
vcs_pth = os.path.join(args.git, "vcs")
merge_branches(vcs_pth, args.vcs)

# Loop through cdms branches
execute_cmd("git clone git://github.com/UV-CDAT/cdms", path=args.git)
cdms_pth = os.path.join(args.git, "cdms")
merge_branches(cdms_pth, args.cdms)

# Loop through metrics branches
execute_cmd("git clone git://github.com/%s" % metrics_repo, path=args.git)
metrics_pth = os.path.join(args.git, metrics_name)
merge_branches(metrics_pth, args.metrics)

f = open("install_in_env.bash", "w")
print("#!/usr/bin/env bash", file=f)
print("source activate %s" % args.env, file=f)
print("conda uninstall -y openblas", file=f)
if args.vcs != ["master"]:
    print("cd %s" % vcs_pth, file=f)
    print("rm -rf build", file=f)
    print("python setup.py install --old-and-unmanageable", file=f)
if args.cdms != ["master"]:
    print("cd %s" % cdms_pth, file=f)
    print("rm -rf build", file=f)
    print("python setup.py install", file=f)
print("cd %s" % metrics_pth, file=f)
print("rm -rf build", file=f)
print("python setup.py install", file=f)
f.close()
execute_cmd("bash install_in_env.bash")


print((
    "You should be good to go, we merged vcs branches:" +
    "'%s' cdms branches: '%s' and metrics branches '%s' into conda env: '%s'" %
    (" ".join(
        args.vcs), " ".join(
            args.cdms), " ".join(
                args.metrics), args.env)))

print("now run")

print(("source activate %s" % args.env))
