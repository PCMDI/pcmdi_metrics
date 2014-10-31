import unittest,test_from_param
import sys
sys.path.append("test/graphics")
import test_portrait

suite= unittest.TestSuite()

suite.addTest(test_from_param.TestFromParam("test/pcmdi/basic_test_parameters_file.py"))
suite.addTest(test_portrait.TestGraphics("test_portrait"))

unittest.TextTestRunner(verbosity=2).run(suite)

