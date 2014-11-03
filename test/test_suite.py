import unittest,test_from_param
import sys
sys.path.append("test/graphics")

suite= unittest.TestSuite()
import os
pth = os.path.dirname(__file__)
suite.addTest(test_from_param.TestFromParam(os.path.join(pth,"pcmdi","basic_test_parameters_file.py")))
try:
    # If we have vcs we can test graphics
    import vcs
    suite.addTest(test_portrait.TestGraphics("test_portrait"))
except:
    pass

unittest.TextTestRunner(verbosity=2).run(suite)

