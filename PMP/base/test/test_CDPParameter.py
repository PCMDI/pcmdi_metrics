import unittest
import sys
from CDP.base.CDPParameter import *


class testCDPParameter(unittest.TestCase):
    def write_file(self, file_name, contents):
        f = open(file_name, 'w')
        f.write(contents)
        f.close()

    def setUp(self):
        # CDPParameter is an abstract base class, so we need to inherit from
        # it to test it.
        class myCDPParameter(CDPParameter):
            def check_values(self):
                pass
        self.cdpparameter = myCDPParameter()

    def test_load_working_parameter(self):
        self.write_file('CDPParameterFile.py', 'var0 = "var0"\n')
        self.cdpparameter.load_parameter_from_py('CDPParameterFile.py')
        self.assertEquals(self.cdpparameter.var0, 'var0')
        os.remove('CDPParameterFile.py')

    def test_load_broken_parameter_with_dot_in_path(self):
        self.write_file('CDP.Parameter.File.Wrong.py', 'var0 = "var0"\n')
        with self.assertRaises(ValueError):
            self.cdpparameter.load_parameter_from_py(
                'CDP.Parameter.File.Wrong.py')
        os.remove('CDP.Parameter.File.Wrong.py')

    def test_load_parameter_with_non_existing_file(self):
        with self.assertRaises(IOError):
            self.cdpparameter.load_parameter_from_py('thisFileDoesntExist.py')

    def test_load_parameter_with_import_in_file(self):
        self.write_file('CDPParameterFile2.py',
                        'import datetime\ndatetime.datetime.now()\n')
        try:
            self.cdpparameter.load_parameter_from_py('CDPParameterFile2.py')
        except:
            self.fail('Test failed with import statement in parameter file.')
        finally:
            os.remove('CDPParameterFile2.py')

if __name__ == '__main__':
    unittest.main()
