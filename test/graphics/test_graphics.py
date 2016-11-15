#!/usr/bin/env python

import unittest
import os
import sys
import pcmdi_metrics

bg = True

class TestGraphics(unittest.TestCase):

    def __init__(self, name):
        super(TestGraphics, self).__init__(name)
        try:
            import vcs
        except:
            raise RuntimeError(
                "Sorry your python is not build with VCS support, cannot generate plots")

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
                "json",
                "v2.0",
                "*.json"))

        json_files += glob.glob(
            os.path.join(
                os.path.dirname(__file__),
                "json",
                "v1.0",
                "*.json"))
        print "JFILES:",json_files
        return pcmdi_metrics.pcmdi.io.JSONs(json_files)


    def test_pcoord(self):
        import vcs
        import vcsaddons

        J=self.loadJSON()
        rms_xyt = J(statistic=["rms_xyt"],season=["ann"],region="global")(squeeze=1)
        x=vcs.init(geometry=(1200,600),bg=bg)
        gm = vcsaddons.createparallelcoordinates(x=x)
        t = vcs.createtemplate()
        to=x.createtextorientation()
        to.angle=-45
        to.halign="right"
        t.xlabel1.textorientation = to.name
        t.reset('x',0.05,0.9,t.data.x1,t.data.x2)
        #t.reset('y',0.5,0.9,t.data.y1,t.data.y2)
        ln = vcs.createline()
        ln.color = [[0,0,0,0]]
        t.legend.line = ln
        t.box1.priority=0
        t.legend.x1 = .91
        t.legend.x2 = .99
        t.legend.y1 = t.data.y1
        t.legend.y2 = t.data.y2

        # Set variable name
        rms_xyt.id = "RMS"

        # Set units of each variables on axis
        rms_xyt.getAxis(-2).units = ["mm/day","mm/day","hPa","W/m2","W/m2","W/m2", "K","K","K","m/s","m/s","m/s","m/s","m"]
        # Sets title
        rms_xyt.title = "Annual Mean Error"

        gm.plot(rms_xyt,template=t,bg=bg)

        src = os.path.join(os.path.dirname(__file__), "testParallelCoordinates.png")
        print src
        fnm = os.path.join(os.getcwd(), "testParallelCoordinates.png")
        x.png(fnm)
        ret = vcs.testing.regression.check_result_image(
            fnm,
            src)
        if ret != 0:
            sys.exit(ret)

    def test_portrait(self):

        # CDAT MODULES
        import pcmdi_metrics.graphics.portraits
        import MV2
        import numpy
        import genutil
        import vcs

        print
        print
        print
        print
        print "---------------------------------------------------"
        print "RUNNING: Portrait test"
        print "---------------------------------------------------"
        print
        print
        print
        print
        # CREATES VCS OBJECT AS A PORTAIT PLOT AND LOADS PLOT SETTINGS FOR
        # EXAMPLE
        x = vcs.init(geometry=(814,606),bg=bg)
        x.portrait()
        # Turn off antialiasing for test suite
        x.setantialiasing(0)

        # PARAMETERS STUFF
        P = pcmdi_metrics.graphics.portraits.Portrait()

        # Turn off verbosity
        P.verbose = False

        P.PLOT_SETTINGS.levels = [-1.e20, -.5, -.4, -.3, -.2, -.1,
                                  0., .1, .2, .3, .4, .5, 1.e20]

        P.PLOT_SETTINGS.x1 = .1
        P.PLOT_SETTINGS.x2 = .85
        P.PLOT_SETTINGS.y1 = .12
        P.PLOT_SETTINGS.y2 = .95

        P.PLOT_SETTINGS.xtic2.y1 = P.PLOT_SETTINGS.y1
        P.PLOT_SETTINGS.xtic2.y2 = P.PLOT_SETTINGS.y2
        P.PLOT_SETTINGS.ytic2.x1 = P.PLOT_SETTINGS.x1
        P.PLOT_SETTINGS.ytic2.x2 = P.PLOT_SETTINGS.x2

        # P.PLOT_SETTINGS.missing_color = 3
        P.PLOT_SETTINGS.logo = os.path.join(sys.prefix,"share","pmp","graphics","png","160915_PCMDI_logo_348x300px.png")
        P.PLOT_SETTINGS.logo.y = .95
        P.PLOT_SETTINGS.logo.x = .93
        P.PLOT_SETTINGS.time_stamp = None
        P.PLOT_SETTINGS.draw_mesh = 'n'
        # P.PLOT_SETTINGS.tictable.font = 3

        x.scriptrun(
            os.path.join(
                sys.prefix,
                "share",
                "pmp",
                "graphics",
                'vcs',
                'portraits.scr'))
        P.PLOT_SETTINGS.colormap = 'bl_rd_12'
        # cols=vcs.getcolors(P.PLOT_SETTINGS.levels,range(16,40),split=1)
        cols = vcs.getcolors(P.PLOT_SETTINGS.levels, range(144, 156), split=1)
        P.PLOT_SETTINGS.fillareacolors = cols

        P.PLOT_SETTINGS.parametertable.expansion = 100

        J = self.loadJSON()

        mods = sorted(J.getAxis("model")[:])
        variables = sorted(J.getAxis("variable")[:])
        print "MODELS:",len(mods),mods
        print "VARS:",len(variables),variables
        # Get what we need
        out1_rel = J(statistic=["rms_xyt"],season=["ann"],region="global")(squeeze=1)

        out1_rel, med = genutil.grower(out1_rel,genutil.statistics.median(out1_rel,axis=1)[0])

        out1_rel[:] = (out1_rel.asma() - med.asma())/ med.asma()

        # ADD SPACES FOR LABELS TO ALIGN AXIS LABELS WITH PLOT
        modsAxis = mods
        variablesAxis = variables

        # LOOP THROUGH LISTS TO ADD SPACES
        for i in range(len(modsAxis)):
            modsAxis[i] = modsAxis[i] + '  '
        for i in range(len(variablesAxis)):
            variablesAxis[i] = variablesAxis[i] + '  '

        yax = [s.encode('utf-8')
               for s in mods]  # CHANGE FROM UNICODE TO BYTE STRINGS

        # GENERATE PLOT
        P.decorate(out1_rel, variables, yax)
        # P.plot(out1_rel,x=x,multiple=1.1,bg=bg)  # FOR PLOTTING TRIANGLES WHEN
        # USING TWO OR MORE REFERENCE DATA SETS
        P.plot(out1_rel, bg=bg, x=x)
        if not bg:
            raw_input("Press enter")
        # x.backend.renWin.Render()

        # END OF PLOTTING

        # SAVE PLOT
        src = os.path.join(os.path.dirname(__file__), "testPortrait.png")
        print src
        fnm = os.path.join(os.getcwd(), "testPortrait.png")
        x.png(fnm)
        ret = vcs.testing.regression.check_result_image(
            fnm,
            src)
        if ret != 0:
            sys.exit(ret)
