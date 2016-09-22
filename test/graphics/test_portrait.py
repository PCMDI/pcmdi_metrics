#!/usr/bin/env python

#
#  RELIES UPON CDAT MODULES
#  PRODUCE SIMPLE PORTRAIT PLOT BASED ON RESULTS FROM PCMDI'S METRICS PACKAGE
#  WRITTEN BY P. GLECKLER, PCMDI/LLNL
#  LAST UPDATE: 7/23/14
#  Cleaned up by C. Doutriaux
# Adapted to unitest format by C. Doutriaux
# See git for change logs
#
import unittest
import checkimage

bg = True

class TestGraphics(unittest.TestCase):

    def __init__(self, name):
        super(TestGraphics, self).__init__(name)

    def test_portrait(self):
        try:
            import vcs
        except:
            raise RuntimeError(
                "Sorry your python is not build with VCS support cannot geenrate portrait plots")

        import json
        # CDAT MODULES
        import pcmdi_metrics
        import pcmdi_metrics.graphics.portraits
        import MV2
        import numpy
        import genutil
        import os
        import sys
        import glob

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
        x = vcs.init()
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

        P.PLOT_SETTINGS.xtic2y1 = P.PLOT_SETTINGS.y1
        P.PLOT_SETTINGS.xtic2y2 = P.PLOT_SETTINGS.y2
        P.PLOT_SETTINGS.ytic2x1 = P.PLOT_SETTINGS.x1
        P.PLOT_SETTINGS.ytic2x2 = P.PLOT_SETTINGS.x2

        # P.PLOT_SETTINGS.missing_color = 3
        # P.PLOT_SETTINGS.logo = None
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


        # LOAD METRICS DICTIONARIES FROM JSON FILES FOR EACH VAR AND STORE AS A
        # SINGLE DICTIONARY
        json_files = glob.glob(
            os.path.join(
                os.path.dirname(__file__),
                "json",
                "v1.0",
                "*.json"))

        json_files += glob.glob(
            os.path.join(
                os.path.dirname(__file__),
                "json",
                "v2.0",
                "*.json"))

        print "JFILES:",json_files
        J = pcmdi_metrics.pcmdi.io.JSONs(json_files)
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
        # x.backend.renWin.Render()

        # END OF PLOTTING

        # SAVE PLOT
        src = os.path.join(os.path.dirname(__file__), "testPortrait.png")
        print src
        fnm = os.path.join(os.getcwd(), "testPortrait.png")
        x.png(fnm)
        ret = checkimage.check_result_image(
            fnm,
            src,
            checkimage.defaultThreshold)
        if ret != 0:
            sys.exit(ret)
