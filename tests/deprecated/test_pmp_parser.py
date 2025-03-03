from __future__ import print_function
import unittest
import os
from pcmdi_metrics.driver.pmp_parser import PMPParser

class PMPParserTest(unittest.TestCase):
    def testProcessTemplatedArgument(self):
        parser = PMPParser(description='Test')

        parser.add_argument("--something", default="something")
        parser.add_argument("--someone", default="someone")
        parser.add_argument("--template", default="%(something)/abc/%(someone)")
        parser.add_argument("-s")  # for nosetest

        parser.add_argument("--with-coverage", default=False, action="store_true",
                            help="run test with code coverage")
        parser.add_argument("--cover-packages", help="package name to get code coverage on")

        A = parser.get_parameter()

        self.assertEqual(A.process_templated_argument("template")(),"something/abc/someone")
        self.assertEqual(A.process_templated_argument("%(someone)/cba/%(something)")(),"someone/cba/something")
