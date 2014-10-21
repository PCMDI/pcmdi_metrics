import unittest,test_from_param

suite= unittest.TestSuite()

suite.addTest(test_from_param.TestFromParam("test/pcmdi/basic_test_parameters_file.py"))

unittest.TextTestRunner(verbosity=2).run(suite)

