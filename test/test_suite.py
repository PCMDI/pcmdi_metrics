import unittest,test_from_param
import sys
sys.path.append("test/graphics")
import test_portrait

suite= unittest.TestSuite()

suite.addTest(test_from_param.TestFromParam("test/pcmdi/basic_test_parameters_file.py"))
try:
    # If we have vcs we can test graphics
    import vcs
    suite.addTest(test_portrait.TestGraphics("test_portrait"))
except:
    pass

unittest.TextTestRunner(verbosity=2).run(suite)

