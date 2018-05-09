#!/usr/bin/env python
from __future__ import print_function
import glob
import sys
import os
import argparse
import multiprocessing
import subprocess
import image_compare
import codecs
import time
import webbrowser
import shlex
import cdat_info

try:
    basestring
except Exception:
    basestring = str

root = os.getcwd()
cpus = multiprocessing.cpu_count()

parser = argparse.ArgumentParser(description="Run PMP tests",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-H", "--html", action="store_true",
                    help="create and show html result page")
parser.add_argument("-p", "--package", action="store_true",
                    help="package test results")
parser.add_argument("-D", "--dropbox", action="store_true",
                    help="upload packaged test results to dropbox (access token must be stored in the envirnoment variable DROPBOX_TOKEN)")
parser.add_argument(
    "-c",
    "--coverage",
    action="store_true",
    help="run coverage (not implemented)")
parser.add_argument(
    "-v",
    "--verbosity",
    default=1,
    choices=[
        0,
        1,
        2],
    type=int,
    help="verbosity output level")
parser.add_argument(
    "-V",
    "--vtk",
    default=None,
    help="conda channel and extras to use for vtk. Command will be 'conda install -c [VTK] vtk-cdat'")
parser.add_argument(
    "-n",
    "--cpus",
    default=cpus,
    type=int,
    help="number of cpus to use")
parser.add_argument(
    "-f",
    "--failed-only",
    action="store_true",
    default=False,
    help="runs only tests that failed last time and are in the list you provide")
parser.add_argument("-U","--update",action="store_true",default=False,help="do not check, simply update results")
parser.add_argument(
    "-T",
    "--traceback",
    default=False,
    action="store_true",
    help="output traceback on exceptions")
parser.add_argument("tests", nargs="*", help="tests to run")

args = parser.parse_args()


def abspath(path, name, prefix):
    import shutil
    full_path = os.path.abspath(os.path.join(os.getcwd(), "..", path))
    if not os.path.exists(name):
        os.makedirs(name)
    new = os.path.join(nm, prefix + "_" + os.path.basename(full_path))
    try:
        shutil.copy(full_path, new)
    except:
        pass
    return new


def findDiffFiles(log):
    i = -1
    file1 = ""
    file2 = ""
    diff = ""
    N = len(log)
    while log[i].find("Source file") == -1 and i > -N:
        i -= 1
    if i > -N:
        file1 = log[i - 1].split()[-1]
        for j in range(i, N):
            if log[j].find("New best!") > -1:
                if log[j].find("Comparing") > -1:
                    file2 = log[j].split()[2]
                else:
                    k = j - 1
                    while log[k].find("Comparing") == -1 and k > -N:
                        k -= 1
                    try:
                        file2 = log[k].split()[2]
                    except:
                        file2 = log[k].split()[1][:-1]+log[j].split()[0]
                        print("+++++++++++++++++++++++++",file2)
            if log[j].find("Saving image diff") > -1:
                diff = log[j].split()[-1]
                # break
    return file1, file2, diff


def run_command(command, join_stderr=True):
    if isinstance(command, basestring):
        command = shlex.split(command)
    if args.verbosity > 0:
        print("Executing %s in %s" % (" ".join(command), os.getcwd()))
    if join_stderr:
        stderr = subprocess.STDOUT
    else:
        stderr = subprocess.PIPE
    P = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=stderr,
        bufsize=0,
        cwd=os.getcwd())
    out = []
    while P.poll() is None:
        read = P.stdout.readline().rstrip().decode("utf-8")
        out.append(read)
        if args.verbosity > 1 and len(read) != 0:
            print(read)
    return P, out


def run_nose(test_name):
    opts = []
    if args.coverage:
        opts += ["--with-coverage"]
    command = ["nosetests", ] + opts + ["-s", test_name]
    start = time.time()
    P, out = run_command(command)
    end = time.time()
    return {test_name: {"result": P.poll(), "log": out, "times": {
        "start": start, "end": end}}}


if args.vtk is not None:
    P, installed_vtk = run_command("conda list vtk-cdat")
    print(installed_vtk)
    while installed_vtk[-1] == "":
        installed_vtk.pop(-1)
    installed_vtk = installed_vtk[-1]
    installed_vtk = installed_vtk.split()
    vtk_name = installed_vtk[0]
    vtk_channel = installed_vtk[-1]
    if args.verbosity > 1:
        print("%s installed from: %s" % (vtk_name, vtk_channel))
    run_command("conda install -f -y -c %s %s" % (args.vtk, vtk_name))

sys.path.append(
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        "tests"))
if len(args.tests) == 0:
    names = glob.glob("tests/test_*.py")
else:
    names = set(args.tests)

if args.failed_only and os.path.exists(os.path.join("tests",".last_failure")):
    f = open(os.path.join("tests",".last_failure"))
    read = f.read().strip()
    try:
        failed = set(eval(read.decode("utf-8")))
    except Exception:
        failed = set(eval(read))
    f.close()
    new_names = []
    for fnm in failed:
        if fnm in names:
            new_names.append(fnm)
    names = new_names

if args.verbosity > 1:
    print(("Names:", names))

if len(names)==0:
    print("No tests to run")
    sys.exit(0)

# Make sure we have sample data
if not os.path.exists("test_data"):
    os.makedirs("test_data")
cdat_info.download_sample_data_files(os.path.join(sys.prefix,"share","pmp","test_data_files.txt"),"test_data")
if args.update:
    os.environ["UPDATE_TESTS"]="True"
if args.traceback:
    os.environ["TRACEBACK"]="True"

p = multiprocessing.Pool(args.cpus)
outs = p.map(run_nose, names)
results = {}
failed = []
for d in outs:
    results.update(d)
    nm = list(d.keys())[0]
    if d[nm]["result"] != 0:
        failed.append(nm)
f = open(os.path.join("tests",".last_failure"),"w")
f.write(repr(failed))
f.close()

if args.verbosity > 0:
    print("Ran %i tests, %i failed (%.2f%% success)" %\
        (len(outs), len(failed), 100. - float(len(failed)) / len(outs) * 100.))
    if len(failed) > 0:
        print("Failed tests:")
        for f in failed:
            print("\t", f)
if args.html or args.package or args.dropbox:
    if not os.path.exists("tests_html"):
        os.makedirs("tests_html")
    os.chdir("tests_html")

    js = image_compare.script_data()

    fi = open("index.html", "w")
    print("<!DOCTYPE html>", file=fi)
    print("""<html><head><title>PMP Test Results %s</title>
    <link rel="stylesheet" type="text/css" href="http://cdn.datatables.net/1.10.13/css/jquery.dataTables.css">
    <script type="text/javascript" src="http://code.jquery.com/jquery-1.12.4.js"></script>
    <script type="text/javascript" charset="utf8"
    src="https://cdn.datatables.net/1.10.13/js/jquery.dataTables.min.js"></script>
    <script>
    $(document).ready( function () {
            $('#table_id').DataTable({
            "order":[[1,'asc'],[0,'asc']],
            "scrollY":"70vh","paging":false,"scrollCollapse":false
            });
                } );
    </script>
    </head>""" % time.asctime(), file=fi)
    print("<body><h1>PMP Test results: %s</h1>" % time.asctime(), file=fi)
    print("<table id='table_id' class='display'>", file=fi)
    print("<thead><tr><th>Test</th><th>Result</th><th>Start Time</th><th>End Time</th><th>Time</th></tr></thead>", file=fi)
    print("<tfoot><tr><th>Test</th><th>Result</th><th>Start Time</th><th>End Time</th><th>Time</th></tr></tfoot>", file=fi)

    for t in sorted(results.keys()):
        result = results[t]
        nm = t.split("/")[-1][:-3]
        print("<tr><td>%s</td>" % nm, end=' ', file=fi)
        fe = codecs.open("%s.html" % nm, "w", encoding="utf-8")
        print("<!DOCTYPE html>", file=fe)
        print("<html><head><title>%s</title>" % nm, file=fe)
        if result["result"] == 0:
            print("<td><a href='%s.html'>OK</a></td>" % nm, end=' ', file=fi)
            print("</head><body>", file=fe)
            print("<a href='index.html'>Back To Results List</a>", file=fe)
        else:
            print("<td><a href='%s.html'>Fail</a></td>" % nm, end=' ', file=fi)
            print("<script type='text/javascript'>%s</script></head><body>" % js, file=fe)
            print("<a href='index.html'>Back To Results List</a>", file=fe)
            print("<h1>Failed test: %s on %s</h1>" % (nm, time.asctime()), file=fe)
            file1, file2, diff = findDiffFiles(result["log"])
            if file1 != "":
                print('<div id="comparison"></div><script type="text/javascript"> ImageCompare.compare(' +\
                    'document.getElementById("comparison"), "%s", "%s"); </script>' % (
                        abspath(file2, nm, "test"), abspath(file1, nm, "source")), file=fe)
                print("<div><a href='index.html'>Back To Results List</a></div>", file=fe)
                print("<div id='diff'><img src='%s' alt='diff file'></div>" % abspath(
                    diff, nm, "diff"), file=fe)
                print("<div><a href='index.html'>Back To Results List</a></div>", file=fe)
        print('<div id="output"><h1>Log</h1><pre>%s</pre></div>' % "\n".join(result[
                                                                                  "log"]), file=fe)
        print("<a href='index.html'>Back To Results List</a>", file=fe)
        print("</body></html>", file=fe)
        fe.close()
        t = result["times"]
        print("<td>%s</td><td>%s</td><td>%s</td></tr>" % (
            time.ctime(t["start"]), time.ctime(t["end"]), t["end"] - t["start"]), file=fi)

    print("</table></body></html>", file=fi)
    fi.close()
    if args.html:
        webbrowser.open("file://%s/index.html" % os.getcwd())
    os.chdir(root)

if args.package or args.dropbox:
    import tarfile
    tnm = "results_%s_%s_%s.tar.bz2" % (os.uname()[0],os.uname()[1],time.strftime("%Y-%m-%d_%H:%M"))
    t = tarfile.open(tnm, "w:bz2")
    t.add("tests_html")
    t.add("tests_html")
    t.close()
    if args.verbosity > 0:
        print("Packaged Result Info in:", tnm)
if args.dropbox: 
    import dropbox
    dbx = dropbox.Dropbox(os.environ.get("DROPBOX_TOKEN",""))
    f=open(tnm,"rb")
    dbx.files_upload(f.read(),"/%s"%tnm)
    f.close()


sys.exit(len(failed))
