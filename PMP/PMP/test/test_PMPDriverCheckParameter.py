import unittest
from CDP.PMP.PMPParameter import *
from CDP.PMP.PMPDriverCheckParameter import *

class testPMPDriverCheckParameter(unittest.TestCase):

    def setUp(self):
        self.pmp_parameter = PMPParameter()


    def test_check_parameter_with_missing_var(self):
        del self.pmp_parameter.vars
        with self.assertRaises(AttributeError):
            PMPDriverCheckParameter.check_parameter(self.pmp_parameter)

if __name__ == '__main__':
    unittest.main()
