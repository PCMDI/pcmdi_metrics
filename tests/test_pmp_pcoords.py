#!/usr/bin/env python

import basepmpgraphics
import os


class TestPCoords(basepmpgraphics.TestGraphics):
    def test_pcoord(self):
        import vcs
        import vcsaddons

        J=self.loadJSON()
        rms_xyt = J(statistic=["rms_xyt"],season=["ann"],region="global")(squeeze=1)
        gm = vcsaddons.createparallelcoordinates(x=self.x)
        t = vcs.createtemplate()
        to = vcs.createtextorientation()
        to.angle=-45
        to.halign="right"
        t.xlabel1.textorientation = to.name
        t.data.list()
        t.reset('x',0.05,0.9,t.data.x1,t.data.x2)
        t.data.list()
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

        gm.plot(rms_xyt,template=t)

        fnm = os.path.join(os.getcwd(), "testParallelCoordinates.png")
        self.checkImage(fnm)

