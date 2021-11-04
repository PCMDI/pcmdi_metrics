#!/usr/bin/env python
import os
import sys
import testsrunner


class PMPTestRunner(testsrunner.TestRunnerBase):
    def _prep_nose_options(self):
        opt = super(PMPTestRunner, self)._prep_nose_options()
        if self.args.update:
            os.environ["UPDATE_TESTS"] = "True"
        if self.args.traceback:
            os.environ["TRACEBACK"] = "True"
        return opt


test_suite_name = "pmp"

workdir = os.getcwd()
runner = PMPTestRunner(
    test_suite_name,
    options=["--update", "--traceback"],
    options_files=["tests/pmp_runtests.json"],
    get_sample_data=True,
    test_data_files_info="share/test_data_files.txt",
)
ret_code = runner.run(workdir)

sys.exit(ret_code)
