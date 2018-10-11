from __future__ import print_function
import unittest
import os
import subprocess
import shlex


class TestFlake8(unittest.TestCase):

    def testFlake8(self):
        pth = os.path.dirname(__file__)
        pth = os.path.join(pth, "..")
        pth = os.path.abspath(pth)
        pth = os.path.join(pth, "src/python")
        nopth = os.path.join(pth, "devel")
        print()
        print()
        print()
        print()
        print("---------------------------------------------------")
        print("RUNNING: flake8 on directory %s" % pth)
        print("---------------------------------------------------")
        print()
        print()
        print()
        print()
        cmd = "flake8 --show-source --statistics " +\
              "--ignore=F999,F405,E121,E123,E126,E226,E24,E704,W504 " +\
              "--max-line-length=120 %s --exclude %s" % (pth,nopth)
        P = subprocess.Popen(shlex.split(cmd),
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out,e = P.communicate()
        out = out.decode("utf-8")
        if out != "":
            print(out)
        self.assertEqual(out, "")
