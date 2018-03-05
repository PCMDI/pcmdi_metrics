#!/usr/bin/env python

import unittest
import os
import sys
import pcmdi_metrics

import checkimage

class TestGraphics(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        self.update = eval(os.environ.get("UPDATE_TESTS","False"))
        self.geometry = {"width": 1200, "height": 600}
        if 'geometry' in kwargs:
            self.geometry = kwargs['geometry']
            del kwargs['geometry']
        self.bg = int(os.environ.get("VCS_BACKGROUND",1))
        if 'bg' in kwargs:
            self.bg = kwargs['bg']
            del kwargs['bg']
        super(TestGraphics, self).__init__(*args, **kwargs)

    def setUp(self):
        try:
            import vcs
        except:
            raise RuntimeError(
                "Sorry your python is not build with VCS support, cannot generate plots")

        # This is for circleci that crashes for any mac bg=True
        self.x=vcs.init(geometry=self.geometry,bg=self.bg)
        self.x.setantialiasing(0)
        if self.geometry is not None:
            self.x.setbgoutputdimensions(self.geometry['width'],
                                         self.geometry['height'],
                                         units="pixels")
        #if not self.bg:
        #    self.x.open()
        self.orig_cwd = os.getcwd()
        self.pngsdir = "tests_png"
        if not os.path.exists(self.pngsdir):
            os.makedirs(self.pngsdir)
        self.basedir = os.path.join(os.path.dirname(__file__), "graphics")


    def tearDown(self):
        os.chdir(self.orig_cwd)
        self.x.clear()
        del(self.x)
        # if png dir is empty (no failures) remove it
        #if glob.glob(os.path.join(self.pngsdir,"*")) == []:
        #    shutil.rmtree(self.pngsdir)

    def checkImage(self,fnm,src=None,threshold=checkimage.defaultThreshold,pngReady=False,pngPathSet=False):
        if src is None:
            src = os.path.join(self.basedir,os.path.basename(fnm))
        if not pngPathSet:
            fnm = os.path.join(self.pngsdir,fnm)
        print "Test file  :",fnm
        print "Source file:",src
        if not pngReady:
            self.x.png(fnm,width=self.x.width, height=self.x.height, units="pixels")
        ret = checkimage.check_result_image(fnm,src,threshold, update_baseline=self.update)
        self.assertEqual(ret,0)
        return ret

    def loadJSON(self):
        """
        # LOAD METRICS DICTIONARIES FROM JSON FILES FOR EACH VAR AND STORE AS A
        # SINGLE DICTIONARY
        """
        import glob
        import json

        json_files = glob.glob(
            os.path.join(
                os.path.dirname(__file__),
                "graphics",
                "json",
                "v2.0",
                "*.json"))

        json_files += glob.glob(
            os.path.join(
                os.path.dirname(__file__),
                "graphics",
                "json",
                "v1.0",
                "*.json"))
        print "JFILES:",json_files
        return pcmdi_metrics.pcmdi.io.JSONs(json_files)
