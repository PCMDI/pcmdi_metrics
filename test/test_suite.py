import unittest
import test_from_param
import sys
import os
pth = os.path.dirname(__file__)
sys.path.append(os.path.join(pth, "graphics"))
import argparse
parser = argparse.ArgumentParser(description="Test suite for pmcdi metrics")

parser.add_argument(
    "-G",
    "--graphics-only",
    action="store_true",
    default=False,
    help="Only run graphics tests")
parser.add_argument(
    "-l",
    "--list",
    action="store_true",
    default=False,
    help="List available tests")
parser.add_argument(
    "-t",
    "--test",
    nargs="*",
    default=None,
    help="Run only this test(s)")
parser.add_argument(
    "-V",
    "--verbose",
    default=False,
    action="store_true",
    help="Verbose output")
parser.add_argument(
    "-T",
    "--traceback",
    default=False,
    action="store_true",
    help="output traceback on exceptions")
parser.add_argument(
    "-U",
    "--update",
    default=False,
    action="store_true",
    help="replace correct test files")

args = parser.parse_args(sys.argv[1:])

params = ["basic_test_parameters_file.py",
          "units_test.py",
          "nosftlf_test.py",
          "gensftlf_test.py",
          "keep_going_on_error_varname_test.py",
          "obs_by_name_test.py",
          "salinity_test.py",
          "region_specs_test.py"
          ]

others = ["flake8", ]
graphics = ["test_portrait", ]

if args.test is not None:
    tests = args.test
elif args.graphics_only:
    tests = graphics
else:
    tests = others + params + graphics

if args.list:
    print "Test that would be run with these options:"
    print tests
    sys.exit()


suite = unittest.TestSuite()

# If we have flake8 then flake8 the code
if "flake8" in tests:
    try:
        import flake8  # noqa
        import test_flake8
        suite.addTest(
            test_flake8.TestFlake8()
        )
    except:
        pass

for t in tests:
    if t in params:
        suite.addTest(
            test_from_param.TestFromParam(
                os.path.join(
                    pth,
                    "pcmdi",
                    t), traceback=args.traceback, update_files=args.update))
    if t in graphics:
        try:
            # If we have vcs we can test graphics
            import vcs  # noqa
            import test_portrait
            suite.addTest(test_portrait.TestGraphics(t))
        except Exception as err:
            print "ERROR import vcs, skipping graphics test (%s)..." % t
            pass

if args.verbose:
    verbosity = 2
else:
    verbosity = 1

results = unittest.TextTestRunner(verbosity=verbosity).run(suite)
if results.wasSuccessful():
    sys.exit()
else:
    sys.exit(1)
