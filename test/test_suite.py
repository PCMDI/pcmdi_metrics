import unittest,test_from_param
import sys,os
pth = os.path.dirname(__file__)
sys.path.append(os.path.join(pth,"graphics"))

suite= unittest.TestSuite()
suite.addTest(test_from_param.TestFromParam(os.path.join(pth,"pcmdi","basic_test_parameters_file.py")))
suite.addTest(test_from_param.TestFromParam(os.path.join(pth,"pcmdi","units_test.py")))
suite.addTest(test_from_param.TestFromParam(os.path.join(pth,"pcmdi","nosftlf_test.py")))
suite.addTest(test_from_param.TestFromParam(os.path.join(pth,"pcmdi","gensftlf_test.py")))
suite.addTest(test_from_param.TestFromParam(os.path.join(pth,"pcmdi","keep_going_on_error_varname_test.py")))
try:
    # If we have vcs we can test graphics
    import vcs,test_portrait
    suite.addTest(test_portrait.TestGraphics("test_portrait"))
except Exception,err:
    print "ERROR import vcs, skipping graphics test..."
    pass

unittest.TextTestRunner(verbosity=2).run(suite)

