import unittest,shutil,shlex,subprocess,os,sys,glob,difflib

class TestFromParam(unittest.TestCase):
  def __init__(self,parameter_file=None,good_files=[]):
    super(TestFromParam,self).__init__("test_from_parameter_file")
    self.param = parameter_file
    self.good_files=good_files

  def setUp(self):
    subprocess.call(shlex.split("pcmdi_metrics_driver.py -p %s" % self.param))
    pass

  def test_from_parameter_file(self):
    #Ok at that point we we can start testing things
    pth,fnm = os.path.split(self.param)
    if pth!="":
        sys.path.append(pth)
    if fnm.lower()[-3:]==".py":
        fnm = fnm[:-3]
    exec("import %s as parameters" % fnm)
    #Ok now let's figure out where the results have been dumped
    pthout = os.path.join(parameters.metrics_output_path,parameters.case_id,"*.json")
    files = glob.glob( pthout )
    for fnm in files:
      nm = os.path.basename(fnm)
      # Ok now we are trying to find the same file
      if self.good_files == []:
        self.good_files = glob.glob("test/pcmdi/*.json")
      ok = True
      for gnm in self.good_files:
        if os.path.basename(gnm)==nm:
          u = difflib.unified_diff(open(fnm).readlines(),open(gnm).readlines())
          for l in u:
            if l[:2]=="- ":
              if l.find("metrics_git_sha1")>-1:
                continue
              else:
                ok = True
    self.assertTrue(ok)
    shutil.rmtree(os.path.join(parameters.metrics_output_path,parameters.case_id))



