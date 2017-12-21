#!/usr/bin/env python

import basepmpgraphics
import os
import pcmdi_metrics.graphics.portraits
import MV2
import numpy
import genutil
import vcs
import sys

class TestPortraits(basepmpgraphics.TestGraphics):
    def __init__(self,*args,**kargs):
        kargs["geometry"] = {"width":814,"height":606}
        super(TestPortraits,self).__init__(*args,**kargs)

    def test_portrait(self):

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
        self.x.portrait()

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
        P.PLOT_SETTINGS.logo = os.path.join(sys.prefix,"share","pmp","graphics","png","PCMDILogo-old_348x300px_72dpi.png")
        P.PLOT_SETTINGS.logo.y = .95
        P.PLOT_SETTINGS.logo.x = .93
        P.PLOT_SETTINGS.logo.width = 85
        P.PLOT_SETTINGS.time_stamp = None
        P.PLOT_SETTINGS.draw_mesh = 'n'
        # P.PLOT_SETTINGS.tictable.font = 3

        self.x.scriptrun(
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
        # USING TWO OR MORE REFERENCE DATA SETS
        P.plot(out1_rel, x=self.x)
        fnm = os.path.join(os.getcwd(), "testPortrait.png")
        self.checkImage(fnm)
