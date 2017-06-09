#!/usr/bin/env python

import basepmpgraphics

bg = True

class TestPCoords(basepmpgraphics.TestGraphics):
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

