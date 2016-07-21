#!/usr/bin/env python

# This is a very simple demo for new users
import subprocess
import requests
import hashlib
import os
import sys
import shlex
import genutil


class bgcolor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def comment(text,cont="[Press enter]"):
    print text
    if cont is None:
        return
    else:
        return raw_input(cont)

def describe(demo_file,colorized=True):
    f = open(demo_file)
    for l in f.xreadlines(): # goes thru the file
        ln = l.strip()
        if ln=="":
            continue
        if ln[0]=="#":  # comment
            while ln[0]=="#":
                ln=ln[1:]
                if ln=="":
                    break
            if colorized:
                bc = bgcolor.OKBLUE
            else:
                bc = ""
            comment(bc+ln.strip()+bgcolor.ENDC,None)
        else:
            if colorized:
                bc = bgcolor.BOLD+bgcolor.UNDERLINE+bgcolor.HEADER
            else:
                bc = ""
            print
            comment(bc+ln+bgcolor.ENDC)
            print
    if colorized:
        bc = bgcolor.OKBLUE
    else:
        bc = ""
    comment(bc+"This ends this parameter file"+bgcolor.ENDC)

def demo(demo_file,title,colorized=True):
    comment("""
        PMP Demo: %s 

    This is a demonstration of the PMP
    It will download some observation and model data for you
    It will then demonstrate how to setup a parameter file to execute PMP on these
    It will run the PMP 
    It will show you where to find the results and how to look at them""" % title)

    cont = comment("""We will now download and untar a small set of data for the demo
    Data will be untarred in the 'pmp_demo' directory created in the current directory""","Continue? [Y/n]")
    if cont.strip().lower() not in ["","y","yes"]:
        sys.exit()

    ## Download data
    demo_pth = os.path.join(os.getcwd(),"pmp_demo")
    if not os.path.exists(demo_pth):
        os.makedirs(demo_pth)
    #  http://oceanonly.llnl.gov/gleckler1/pmp-demo-data/pmpv1.1_demodata.tar
    tar_filename = "pmpv1.1_demodata.tar"
    tar_pth = os.path.join(demo_pth,tar_filename)

    good_md5 = "a6ef8f15457378ff36fd46e8fbf5f157"

    attempts = 0
    while attempts < 3:
        md5 = hashlib.md5()
        if os.path.exists(tar_filename):
            f = open(tar_filename)
            md5.update(f.read())
            if md5.hexdigest() == good_md5:
                attempts = 5
                continue
        print "Downloading: ", tar_filename
        r = requests.get("http://oceanonly.llnl.gov/gleckler1/pmp-demo-data/pmpv1.1_demodata.tar", stream=True)
        with open(tar_pth, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter local_filename keep-alive new chunks
                    f.write(chunk)
                    md5.update(chunk)
        f.close()
        if md5.hexdigest() == good_md5:
            attempts = 5
        else:
            attempts += 1

    comment("Successfuly downloaded demo tarball\nNow untarring it", None)

    tar_process = subprocess.Popen(shlex.split("tar xvf %s"%tar_pth),cwd=demo_pth)
    tar_process.wait()

    comment("Success! Files are now untarred in %s\nLet's run this demo!\n" % demo_pth,None)
    comment("""The PMP package runs off a 'parameter' file which needs to be edited by the user
    Please kindly take a look at our sample parameter file in: %s""" % demo_file)

    describe(demo_file)
    cmd = "pcmdi_metrics_driver.py -p %s" % demo_file
    comment("We will now run the pmp using this parameter file\nTo do so we are using the follwoing command\n%s" % cmd)
    pmp = subprocess.Popen(shlex.split(cmd))
    sys.path.insert(0,os.path.dirname(demo_file))
    exec("import %s as pmp_param" % os.path.basename(demo_file)[:-3])
    pmp.wait()
    loc = genutil.StringConstructor(os.path.join(pmp_param.metrics_output_path))
    for att in ["case_id","model_version","period","realization","period"]:
        if hasattr(pmp_param,att):
            setattr(loc,att,getattr(pmp_param,att))
    comment("You can now look at the results in: %s%s%s" % (bgcolor.HEADER+bgcolor.BOLD,loc(),bgcolor.ENDC))

