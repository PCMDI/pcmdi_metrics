from __future__ import print_function
import unittest
import basepmp
import cdat_info
import subprocess
import shlex
import os
import cdms2
import numpy
import json
import sys


class DiurnalTest(basepmp.PMPTest):

    def setUp(self):
        if "COVERAGE_PROCESS_START" in os.environ:
            runner = "coverage run"
        else:
            runner = "python"
        runner += " {}/".format(os.path.join(sys.prefix, "bin"))
        self.runner = runner

    def assertSame(self,a,b):
        self.assertTrue(numpy.ma.allclose(a,b))

    def compare_nc(self,test_name):
        print("Checking integrity of",test_name)
        self.assertTrue(os.path.exists(os.path.join("test_data",test_name)))
        good_name = test_name.replace("test_data","tests/diurnal")

        test_out = cdms2.open(os.path.join("test_data",test_name))
        good_out = cdms2.open(os.path.join("tests/diurnal",test_name))

        print("Checking same variables are present as in {}".format(good_name))
        self.assertEqual(list(test_out.variables.keys()),list(good_out.variables.keys()))

        for v in list(good_out.variables.keys()):
            print("Checking variable {} is correct".format(v))
            test = test_out(v)
            good = good_out(v)
            self.assertSame(test,good)
        
    def teestDiurnaliComputeStdDailyMean(self):
        data_pth = cdat_info.get_sampledata_path()
        cmd = '{}computeStdDailyMeansWrapped.py --num_workers=1 --mp {} --rd test_data/results/nc -t "sample_data_pr_%(model).nc" -m7'.format(self.runner, data_pth)
        p = subprocess.Popen(shlex.split(cmd))
        p.communicate()

        self.compare_nc("results/nc/pr_CMCC_Jul_1999-2005_std_of_dailymeans.nc")

    def teestFourierDiurnalAllGridWrapped(self):
        cmd = '{}fourierDiurnalAllGridWrapped.py --num_workers=1 --mp tests/diurnal/results/nc --rd test_data/results/nc -m7'.format(self.runner)
        p = subprocess.Popen(shlex.split(cmd))
        p.communicate()
        self.compare_nc("results/nc/pr_CMCC_Jul_1999-2005_tmean.nc")
        self.compare_nc("results/nc/pr_CMCC_Jul_1999-2005_tS.nc")
        self.compare_nc("results/nc/pr_CMCC_Jul_1999-2005_S.nc")

    def testDiurnalStdDailyVariance(self):
        self.runJsoner("std_of_dailymeansWrappedInOut.py","pr_Jul_1999_2005_std_of_dailymeans.json","std_of_dailymeans")

    def runJsoner(self,script,json_file,ext):
        cmd = '{}{} --num_workers=1 --region_name=TROPICS --lat1=-30. --lat2=30. --lon1=0. --lon2=360 --mp tests/diurnal/results/nc --rd test_data/results/jsons -m7 -t "pr_%(model)_%(month)_%(firstyear)-%(lastyear)_{}.nc"'.format(self.runner, script, ext)
        p = subprocess.Popen(shlex.split(cmd))
        p.communicate()
        cmd = '{}{} --append --mp tests/diurnal/results/nc --rd test_data/results/jsons -m7 -t "pr_%(model)_%(month)_%(firstyear)-%(lastyear)_{}.nc"'.format(self.runner, script, ext)
        p = subprocess.Popen(shlex.split(cmd))
        p.communicate()
        good = open("tests/diurnal/results/json/{}".format(json_file))
        test = open("test_data/results/jsons/{}".format(json_file))
        good_nm = "tests/diurnal/results/json/{}".format(json_file)
        test_nm = "test_data/results/jsons/{}".format(json_file)
        self.assertSimilarJsons(test_nm, good_nm)
        """
        test = json.load(test)
        good = json.load(good)
        self.assertEqual(test["RESULTS"],good["RESULTS"])
        """
    def teestCompositeDiurnalStatisticsWrapped(self):
        data_pth = cdat_info.get_sampledata_path()
        cmd = '{}compositeDiurnalStatisticsWrapped.py --num_workers=1 --mp {} --rd test_data/results/nc -t "sample_data_pr_%(model).nc" -m7'.format(self.runner, data_pth)
        print("CCOOOMOMMOMONFDFDDFFDSASFGFDSAFGFFGSDFFGFSG", cmd)
        p = subprocess.Popen(shlex.split(cmd))
        p.communicate()
        self.compare_nc("results/nc/pr_CMCC_Jul_1999-2005_diurnal_avg.nc")
        self.compare_nc("results/nc/pr_CMCC_Jul_1999-2005_diurnal_std.nc")
        self.compare_nc("results/nc/pr_CMCC_LocalSolarTimes.nc")

    def teestStd_of_hourlyvaluesWrappedInOut(self):
        self.runJsoner("std_of_hourlyvaluesWrappedInOut.py","pr_Jul_1999-2005_std_of_hourlymeans.json","diurnal_std")

    def teestStd_of_meandiurnalcycWrappedInOut(self):
        self.runJsoner("std_of_meandiurnalcycWrappedInOut.py","pr_Jul_1999-2005_std_of_meandiurnalcyc.json","diurnal_avg")

    def teestSavg_fourierWrappedInOut(self):
        self.runJsoner("savg_fourierWrappedInOut.py","pr_Jul_1999-2005_savg_DiurnalFourier.json","S")

    def teestfourierDiurnalGridpoints(self):
        cmd = '{}fourierDiurnalGridpoints.py --num_workers=1 --mp tests/diurnal/results/nc --rd test_data/results/ascii'.format(self.runner)
        p = subprocess.Popen(shlex.split(cmd))
        p.communicate()
        self.assertTrue(os.path.exists("test_data/results/ascii/pr_Jul_1999-2005_fourierDiurnalGridPoints.asc"))
