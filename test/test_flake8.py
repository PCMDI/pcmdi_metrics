import unittest
import os
import subprocess
import shlex


class TestFlake8(unittest.TestCase):

    def __init__(self):
        super(TestFlake8, self).__init__("flake8")

    def flake8(self):
        pth = os.path.dirname(__file__)
        pth = os.path.join(pth, "..")
        pth = os.path.abspath(pth)
        pth = os.path.join(pth, "src")
        print
        print
        print
        print
        print "---------------------------------------------------"
        print "RUNNING: flake8 on directory %s" % pth
        print "---------------------------------------------------"
        print
        print
        print
        print
        P = subprocess.Popen(shlex.split("flake8 --max-line-length=120 %s" % pth),
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        P.wait()
        out = P.stdout.read()
        if out != "":
            print out
        self.assertTrue(out == "")
