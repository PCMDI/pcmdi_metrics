#!/usr/bin/env python
import sys
import os

bd,nm=os.path.split(sys.argv[0])
print bd,nm
sys.path.insert(0,bd)
import pmp_demo
pmp_demo.demo(os.path.join(sys.prefix,"share","pmp","demo","pmp_input_parameters_demo1.py"),"simple-test1")
