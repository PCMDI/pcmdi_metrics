#!/usr/bin/env python

from __future__ import print_function
import MV2
import cdms2
import vcs
import genutil
import glob
import numpy
import time
from genutil import StringConstructor
import os
import pkg_resources
pmp_egg_path = pkg_resources.resource_filename(pkg_resources.Requirement.parse("pcmdi_metrics"), "share")



def is_dark_color_type(R, G, B, A):
    """figure out if a color is dark or light alpha is ignored"""
    # Counting the perceptive luminance - human eye favors green color...
    a = 1 - (0.299 * R + 0.587 * G + 0.114 * B) / 100.
    return a > .5


class Values(object):
    __slots__ = ("show", "array", "text",
                 "lightcolor", "darkcolor", "format")

    def __init__(self, show=False, array=None,
                 lightcolor="white", darkcolor="black", format="{0:.2f}"):
        self.show = show
        self.array = array
        self.text = vcs.createtext()
        self.text.valign = "half"
        self.text.halign = "center"
        self.lightcolor = lightcolor
        self.darkcolor = darkcolor
        self.format = format


class Xs(object):
    __slots__ = ("x1", "x2")

    def __init__(self, x1, x2):
        self.x1 = x1
        self.x2 = x2


class Ys(object):
    __slots__ = ("y1", "y2")

    def __init__(self, y1, y2):
        self.y1 = y1
        self.y2 = y2


class XYs(object):
    __slots__ = ("x1", "x2", "y1", "y2")

    def __init__(self, x1, x2, y1, y2):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2


class Plot_defaults(object):
    __slots__ = ["x1", "x2", "y1", "y2", "levels", "colormap",
                 "fillareacolors", "legend", "_logo",
                 "xticorientation", "yticorientation",
                 "parameterorientation", "tictable",
                 "parametertable", "draw_mesh", "values",
                 "missing_color", "xtic1", "xtic2", "ytic1", "ytic2",
                 "time_stamp"]

    def getlogo(self):
        return self._logo

    def setlogo(self, value):
        if value is None or isinstance(value, str):
            self._logo = vcs.utils.Logo(value)

    logo = property(getlogo, setlogo)

    def __init__(self):
        self.x1 = .12
        self.x2 = .84
        self.y1 = .17
        self.y2 = .8
        self.levels = None
        self.colormap = None
        self.fillareacolors = None
        self.legend = XYs(.89, .91, self.y1, self.y2)
        # X ticks
        self.xticorientation = vcs.createtextorientation()
        self.xticorientation.angle = 360 - 90
        self.xticorientation.halign = 'right'
        self.xticorientation.height = 10
        # Y ticks
        self.yticorientation = vcs.createtextorientation()
        self.yticorientation.angle = 0
        self.yticorientation.halign = 'right'
        self.yticorientation.height = 10
        # Ticks table
        self.tictable = vcs.createtexttable()
        # parameters text settings
        self.parameterorientation = vcs.createtextorientation()
        self.parameterorientation.angle = 0
        self.parameterorientation.halign = 'center'
        self.parameterorientation.height = 20
        self.parametertable = vcs.createtexttable()
        # values in cell setting
        self.values = Values()
        # Defaults
        self.draw_mesh = 'y'
        self.missing_color = 3
        self.xtic1 = Ys(None, None)
        self.xtic2 = Ys(None, None)
        self.ytic1 = Xs(None, None)
        self.ytic2 = Xs(None, None)
        # Set the logo textorientation
        self.logo = None
        # Set the time stamp
        time_stamp = vcs.createtext()
        time_stamp.height = 10
        time_stamp.halign = 'center'
        time_stamp.path = 'right'
        time_stamp.valign = 'half'
        time_stamp.x = [0.9]
        time_stamp.y = [0.96]
        self.time_stamp = time_stamp


class Portrait(object):
    __slots_ = [
        "verbose", "files_structure",
        "exclude", "parameters_list",
        "dummies", "auto_dummies", "grouped",
        "slaves", "altered", "aliased",
        "portrait_types", "PLOT_SETTINGS", "x", "bg"
    ]

    def __init__(self, files_structure=None, exclude=[], **kw):
        ''' initialize the portrait object, from file structure'''
        if "x" in kw:
            self.x = kw["x"]
        else:
            self.x = vcs.init()
        scr_file = os.path.join(
        pmp_egg_path,
        "pmp",
        "graphics",
        'vcs',
        'portraits.scr')
        self.x.scriptrun(scr_file)
        self.verbose = False  # output files looked for to the screen
        self.files_structure = files_structure
        self.exclude = exclude
        # First determine the list of parameters on which we can have a
        # portrait
        self.parameters_list = []
        self.dummies = []
        self.auto_dummies = []
        self.grouped = []
        self.slaves = {}
        self.altered = {}
        self.aliased = {}
        self.portrait_types = {}
        self.PLOT_SETTINGS = Plot_defaults()
        if files_structure is not None:
            sp = files_structure.split('%(')
            for s in sp:
                i = s.find(')')
                if i > -1:  # to avoid the leading path
                    val = s[:i]
                    if not (
                        val in self.parameters_list or
                            val in ['files_structure', 'exclude']):
                        self.parameters_list.append(s[:i])
        self.parameters_list.append('component')
        self.parameters_list.append('statistic')
        self.parameters_list.append('time_domain')
        for p in self.parameters_list:
            setattr(self, p, None)
        for k in list(kw.keys()):
            setattr(self, k, kw[k])

    def alter_parameter(
            self, parameter=None, x=None, y=None, size=None, color=None):
        if parameter is not None:
            self.altered[parameter] = {
                'x': x,
                'y': y,
                'size': size,
                'color': color}
        else:
            if color is not None:
                self.PLOT_SETTINGS.parametertable.color = color
            if size is not None:
                self.PLOT_SETTINGS.parameterorientation.size = size

    def string_construct(self, nms):
        n = nms[0]
        if n not in list(self.slaves.keys()):
            t1 = [n + ' ' for nn in getattr(self, n)]
            t2 = [str(nn) + ' ' for nn in getattr(self, n)]
        else:
            slavs = self.slaves[n]
            nm = ''
            for i in slavs:
                nm = nm + ' ' + i
            t1 = [n + nm + ' ' for nn in getattr(self, n)]
            v1 = [res for res in getattr(self, n)]
            vals = []
            for i in range(len(v1)):
                tmp = ''
                for a in v1[i]:
                    if not a == '':
                        tmp += ' ' + str(a) + ' '
                    else:
                        tmp += ' NONE' + ' '
                vals.append(tmp)
            t2 = [nn for nn in vals]
        for n in nms[1:]:
            if n not in list(self.slaves.keys()):
                t1 = [' ' + t + ' ' + n for t in t1 for nn in getattr(self, n)]
                t2 = [
                    ' ' +
                    t +
                    ' ' +
                    str(nn) for t in t2 for nn in getattr(
                        self,
                        n)]
            else:
                slavs = self.slaves[n]
                nm = ' '
                for i in slavs:
                    nm = ' ' + nm + ' ' + i
                t1b = [n + nm for nn in getattr(self, n)]
                v1 = [res for res in getattr(self, n)]
                vals = []
                for i in range(len(v1)):
                    tmp = ''
                    for a in v1[i]:
                        if not a == '':
                            tmp += ' ' + str(a)
                        else:
                            tmp += ' NONE'
                    vals.append(tmp)
                t2b = [nn for nn in vals]
                t1 = [t + tb for t in t1 for tb in t1b]
                t2 = [t + tb for t in t2 for tb in t2b]
        t3 = []
        t1 = t1[0]
        sp = t1.split()
        n = len(sp)
        for tmp in t2:
            if isinstance(tmp, int):
                tmp = str(tmp)
            t = []
            tt = tmp.split()
            for i in range(n):
                t.append(self.makestring(sp[i], tt[i]))
            t3.append("%%%".join(t))
        return t1, t2, t3

    def set(self, portrait_type, parameter=None, values=None):
        if portrait_type.lower() == 'absolute':
            if 'relative' in list(self.portrait_types.keys()):
                del(self.portrait_types['relative'])
        elif portrait_type.lower() == 'relative':
            if not isinstance(parameter, str):
                raise 'Parameter must be a string'
            if not isinstance(values, (list, tuple)):
                raise 'values must be a list or tuple'
            self.portrait_types['relative'] = [parameter, values]
        elif portrait_type.lower() == 'difference':
            if not isinstance(parameter, str):
                raise 'Parameter must be a string'
            if not isinstance(values, (list, tuple)):
                raise 'values must be a list or tuple'
            self.portrait_types['difference'] = [parameter, values]
        elif portrait_type.lower() in ['mean', 'average']:
            if not isinstance(parameter, str):
                raise 'Parameter must be a string'
            if not isinstance(values, (list, tuple)):
                raise 'values must be a list or tuple'
            self.portrait_types['mean'] = [parameter, values]
        else:
            raise RuntimeError(
                'Error type:"%s" not supported at this time' %
                (portrait_type))

    def dummy(self, parameter, which_dummy=''):
        ''' Sets a parameter as dummy, i.e. all possible values will be used'''
        val = getattr(self, which_dummy + 'dummies')
        if parameter not in val:
            val.append(parameter)
            setattr(self, which_dummy + 'dummies', val)
            setattr(self, parameter, None)

    def group(self, param1, param2):
        ''' sets 2 multiple values of parameters on the same axis'''
        added = 0
        for i in range(len(self.grouped)):
            g = self.grouped[i]
            if param1 in g:
                if param2 not in g:
                    added = 1
                    self.grouped[i].append(param2)
            elif param2 in g:
                added = 1
                self.grouped[i].append(param1)
        if not added:
            self.grouped.append([param1, param2])

    def slave(self, master, slave):
        ''' defines a parameter as a slave of a master parameter'''
        if master in list(self.slaves.keys()):
            v = self.slaves[master]
            if slave not in v:
                v.append(slave)
                self.dummy(slave, which_dummy='auto_')
                self.slaves[master] = v
        else:
            self.slaves[master] = [slave]
            self.dummy(slave, which_dummy='auto_')

    def alias(self, parameter, values):
        if isinstance(values, dict):
            self.aliased[parameter] = values
        else:
            oldvalue = getattr(self, parameter)
            if parameter in list(self.slaves.keys()):
                ov = []
                for n in oldvalue:
                    ov.append(n[0])
                oldvalue = ov
            n = len(oldvalue)
            if len(values) != n:
                raise 'Error aliasing ' + parameter + ' you submitted ' + \
                    str(len(values)) + ' aliases but it should be:' + str(n)
            dic = {}
            for i in range(n):
                dic[oldvalue[i]] = values[i]
            self.aliased[parameter] = dic

    def makestring(self, parameter, value):
        if parameter in list(self.aliased.keys()):
            dic = self.aliased[parameter]
            if value in list(dic.keys()):
                return dic[value]
            else:
                return value
        else:
            return value

    def makeaxis(self, names, axis_length):
        """
        Create the axis with the names, etc.. .for portrait plot
        Usage:
        makeaxis(self,names,axis_length)
        Returns:
        a cdms axis
        """
        # Now creates the axis names
        t1, t2, t3 = self.string_construct(names)

        sp1 = t1.split()
        axis_names = []
        for i in range(len(t2)):
            nm = ''
            sp2 = t3[i].split('%%%')
            for j in range(len(sp2)):
                if not sp1[j] in self.dummies and not sp2[j] == 'NONE':
                    # print sp2,j
                    if not sp2[j][0] == '_':
                        nm += ' ' + sp2[j]
                    else:
                        nm += ' ' + sp2[j][1:]
            axis_names.append(nm)
        dic = {}
        for i in range(len(axis_names)):
            dic[i] = axis_names[i]
        y = cdms2.createAxis(list(range(axis_length)))
        y.names = repr(dic)
        nm = []
        for t in sp1:
            if t not in self.dummies:
                nm.append(t)
        nm = "___".join(nm)
        y.id = nm
        return y

    def rank(self, data, axis=0):
        if axis not in [0, 1]:
            if not isinstance(axis, str):
                raise 'Ranking error, axis can only be 1 or 2 or name'
            else:
                nms = data.getAxisIds()
                for i in range(len(nms)):
                    nm = nms[i]
                    if axis in nm.split('___'):
                        axis = i
                if axis not in [0, 1]:
                    raise 'Ranking error, axis can only be 1 or 2 or name'
        if data.ndim > 2:
            raise "Ranking error, array can only be 2D"

        if axis == 1:
            data = MV2.transpose(data)
        a0 = MV2.argsort(data.filled(1.E20), axis=0)
        n = a0.shape[0]
        b = MV2.zeros(a0.shape, MV2.float)
        sh = a0[1].shape
        for i in range(n):
            Indx = MV2.ones(sh) * i
            c = MV2.array(a0[i].filled(n - 1))
            b = genutil.arrayindexing.set(b, c, Indx)

        m = data.mask
        if m is not None:
            b = MV2.masked_where(m, b)
        else:
            b = MV2.array(b)
        n = MV2.count(b, 0)
        n.setAxis(0, b.getAxis(1))
        b, n = genutil.grower(b, n)
        b = 100. * b / (n - 1)
        b.setAxisList(data.getAxisList())
        if axis == 1:
            b = MV2.transpose(b)
            data = MV2.transpose(data)
        return b

    def rank_nD(self, data, axis=0):
        if axis not in [0, 1]:
            if not isinstance(axis, str):
                raise 'Ranking error, axis can only be 1 or 2 or name'
            else:
                nms = data.getAxisIds()
                for i in range(len(nms)):
                    nm = nms[i]
                    if axis in nm.split('___'):
                        axis = i
                if axis not in [0, 1]:
                    raise 'Ranking error, axis can only be 1 or 2 or name'

        if axis != 0:
            data = data(order=(str(axis) + '...'))
        a0 = MV2.argsort(data.filled(1.E20), axis=0)
        n = a0.shape[0]
        b = MV2.zeros(a0.shape, MV2.float)
        sh = a0[1].shape
        for i in range(n):
            Indx = MV2.ones(sh) * i
            c = MV2.array(a0[i].filled(n - 1))
            b = genutil.arrayindexing.set(b, c, Indx)
        m = data.mask
        if m is not None:
            b = MV2.masked_where(m, b)
        else:
            b = MV2.array(b)
        n = MV2.count(b, 0)
        n.setAxisList(b.getAxisList()[1:])
        b, n = genutil.grower(b, n)
        b = 100. * b / (n - 1)
        b.setAxisList(data.getAxisList())
        if axis != 0:
            st = ''
            for i in range(axis):
                st += str(i + 1)
            st += '0...'
            data = data(order=st)
            b = b(order=st)
        return b

    def get(self):
        if 'difference' in list(self.portrait_types.keys()):
            d = self.portrait_types['difference']
            setattr(self, d[0], d[1][0])
            a1 = self._get()
            setattr(self, d[0], d[1][1])
            a2 = self._get()
            return a1 - a2
        elif 'mean' in list(self.portrait_types.keys()):
            d = self.portrait_types['mean']
            setattr(self, d[0], d[1][0])
            # This picked up by flake8
            # probably needs double check
            # used to be +=
            tmp = self._get()
            for v in d[1][1:]:
                setattr(self, d[0], v)
                tmp += self._get()
            return tmp / len(d[1])
        else:
            return self._get()

    def _get(self):
        if 'relative' in list(self.portrait_types.keys()):
            d = self.portrait_types['relative']
            vals = d[1]
            real_value = getattr(self, d[0])
            real = self.__get()
            setattr(self, d[0], vals[0])
            a0 = self.__get()
            sh = list(a0.shape)
            sh.insert(0, 1)
            a0 = MV2.reshape(a0, sh)
            for v in vals[1:]:
                setattr(self, d[0], v)
                tmp = self.__get()
                tmp = MV2.reshape(tmp, sh)
                a0 = MV2.concatenate((a0, tmp))
            a0 = MV2.sort(a0, 0).filled()
            real2 = real.filled()
            a0 = MV2.reshape(a0, (a0.shape[0], sh[1] * sh[2]))
            real2 = MV2.reshape(real2, (sh[1] * sh[2],))
            a0 = MV2.transpose(a0)
            indices = []
            for i in range(len(real2)):
                indices.append(MV2.searchsorted(a0[i], real2[i]))
            indices = MV2.array(indices)
            indices = MV2.reshape(indices, (sh[1], sh[2]))
            if not ((real.mask is None) or (real.mask is MV2.nomask)):
                indices = MV2.masked_where(real.mask, indices)
            a = MV2.masked_equal(a0, 1.e20)
            a = MV2.count(a, 1)
            a = MV2.reshape(a, indices.shape)
            indices = indices / a * 100
            setattr(self, d[0], real_value)
            indices.setAxisList(real.getAxisList())
# print indices.shape
            return indices
        else:
            return self.__get()

    def __get(self):
        nfree = 0
        names = []
        for p in self.parameters_list:
            if p not in self.dummies and p not in self.auto_dummies:
                v = getattr(self, p)
                if v is None \
                        or \
                        (isinstance(v, (list, tuple)) and len(v) > 1):
                    already = 0
                    for pn in names:
                        if p == pn:
                            already = 1
                        elif isinstance(pn, list):
                            if p in pn:
                                already = 1
                    if already == 0:
                        nfree += 1
                        added = 0
                        for g in self.grouped:
                            if p in g:
                                names.append(g)
                                added = 1
                        if added == 0:
                            names.append(p)

        if nfree != 2:
            raise 'Error MUST end up with 2 multiple values ! (we have ' + str(
                nfree) + ':' + str(names) + ')'
        # Now determines length of each axis
        axes_length = [1, 1]
        # First make sure with have 2 list of parameters
        for i in range(2):
            if not isinstance(names[i], list):
                names[i] = [names[i]]
            for n in names[i]:
                v = getattr(self, n)
                if v is None:
                    if n == 'component':
                        axes_length[i] *= 28
                    elif n == 'time_domain':
                        axes_length[i] *= 19
                    else:
                        raise 'Error, ' + n + \
                            ' is not defined correctly, please' + \
                            ' specify which values you wish to extract'
                else:
                    axes_length[i] *= len(v)
        # Creates the dummy array
        output = MV2.ones((axes_length[0], axes_length[1]))
        # Now mask everywhere
        output = MV2.masked_equal(output, 1)
        # Indices for filling
        i = 0
        j = 0
        # First creates the filler object and sets all the fixed values !
        F = StringConstructor(self.files_structure)
        # Ok let's fill it
        for p in self.parameters_list:
            if p not in self.dummies and p not in self.auto_dummies:
                v = getattr(self, p)
                if isinstance(v, (list, tuple)):
                    if len(v) == 1:
                        v = v[0]
                        if p in list(self.slaves.keys()):
                            # vslvs = v[1:]
                            v = v[0]
                        setattr(F, p, v)
                        if p in list(self.slaves.keys()):
                            slvs = self.slaves[p]
                            for js in range(len(slvs)):
                                s = slvs[js]
                                setattr(F, s, slvs[js])
                    else:
                        setattr(F, p, '*')
                else:
                    if p in list(self.slaves.keys()):
                        # vslvs = v[1:]
                        v = v[0]
                    setattr(F, p, v)
                    if p in list(self.slaves.keys()):
                        slvs = self.slaves[p]
                        for js in range(len(slvs)):
                            s = slvs[js]
                            setattr(F, s, slvs[js])
            else:
                setattr(F, p, '*')

        # fnms=F()
        nms = names[0] + names[1]

        t1, t2, t3 = self.string_construct(nms)
        output = output.ravel()
        sp1 = t1.split()
        n = len(sp1)
        for i in range(len(t2)):
            sp2 = t2[i].split()
            for j in range(n):
                v = sp2[j]
                if sp1[j] == 'time_domain':
                    try:
                        v = int(v)
                    except Exception:
                        pass
                if v == 'NONE':
                    v = ''
                setattr(F, sp1[j], v)
            #  print 'Search string is:',fnms
            # f=os.popen('ls '+F()).readlines()
            # ip,op,ep=os.popen3('ls '+F())
            if self.verbose:
                print('command line:', F())
            # f=op.readlines()
            f = glob.glob(F())
            # print 'F is:',f
            files = []
            for file in f:
                files.append(file)
                for e in self.exclude:
                    if file.find(e) > -1:
                        files.pop(-1)
                        break
            if self.verbose:
                print('files:', files)
            try:
                # now we get the one value needed in this file
                f = cdms2.open(files[0])
                V = f[F.statistic]
                component = F.component
                time_domain = F.time_domain
                if isinstance(component, str):
                    dic = eval(f.components)
                    for k in list(dic.keys()):
                        if dic[k] == F.component:
                            component = k
                if isinstance(F.time_domain, str):
                    dic = eval(f.time_domain)
                    for k in list(dic.keys()):
                        if dic[k] == F.time_domain:
                            time_domain = k
                value = V(
                    time_domain=time_domain,
                    component=component,
                    squeeze=1)
                output[i] = value
                # In case sometihng goes wrong (like modle not processed or
                # inexsitant for this var, etc...)
                f.close()
            except Exception:
                pass
        output = MV2.reshape(output, (axes_length[0], axes_length[1]))
        output.id = 'portrait plot'

        yaxis = self.makeaxis(names[0], axes_length[0])
        xaxis = self.makeaxis(names[1], axes_length[1])
        output.setAxis(0, yaxis)
        output.setAxis(1, xaxis)

        # Makes the dim with the most element on the X axis
        if axes_length[0] > axes_length[1]:
            output = MV2.transpose(output)

        return output

    def decorate(self, output, ynm, xnm):
        x = cdms2.createAxis(list(range(len(xnm))))
        y = cdms2.createAxis(list(range(len(ynm))))

        try:
            del(x.name)
            del(y.name)
            del(output.name)
        except Exception:
            pass

        nm = '___'.join(xnm)
        x.id = nm
        dic = {}
        for i in range(len(xnm)):
            dic[i] = xnm[i]
        x.names = repr(dic)
        nm = '___'.join(ynm)
        y.id = nm
        y.original_id = output.getAxis(0,).id
        output.setAxis(0, y)
        dic = {}
        for i in range(len(ynm)):
            dic[i] = ynm[i]
        y.names = repr(dic)
        x.original_id = output.getAxis(1,).id
        output.setAxis(1, x)

        return

    def generateTemplate(self):
        template = vcs.createtemplate()
        # Now sets all the things for the template...
        # Sets a bunch of template attributes to off
        for att in [
            'line1', 'line2', 'line3', 'line4',
            'box2', 'box3', 'box4',
            'min', 'max', 'mean',
            'xtic1', 'xtic2',
            'ytic1', 'ytic2',
            'xvalue', 'yvalue', 'zvalue', 'tvalue',
            'xunits', 'yunits', 'zunits', 'tunits',
            'source', 'title', 'dataname',
        ]:
            a = getattr(template, att)
            setattr(a, 'priority', 0)
        for att in [
            'xname', 'yname',
        ]:
            a = getattr(template, att)
            setattr(a, 'priority', 0)

        template.data.x1 = self.PLOT_SETTINGS.x1
        template.data.x2 = self.PLOT_SETTINGS.x2
        template.data.y1 = self.PLOT_SETTINGS.y1
        template.data.y2 = self.PLOT_SETTINGS.y2
        template.box1.x1 = self.PLOT_SETTINGS.x1
        template.box1.x2 = self.PLOT_SETTINGS.x2
        template.box1.y1 = self.PLOT_SETTINGS.y1
        template.box1.y2 = self.PLOT_SETTINGS.y2
        template.xname.y = self.PLOT_SETTINGS.y2 + .02
        template.yname.x = self.PLOT_SETTINGS.x2 + .01
        template.xlabel1.y = self.PLOT_SETTINGS.y1
        template.xlabel2.y = self.PLOT_SETTINGS.y2
        template.xlabel1.texttable = self.PLOT_SETTINGS.tictable
        template.xlabel2.texttable = self.PLOT_SETTINGS.tictable
        template.xlabel1.textorientation = \
            self.PLOT_SETTINGS.xticorientation
        template.xlabel2.textorientation = \
            self.PLOT_SETTINGS.xticorientation
        template.ylabel1.x = self.PLOT_SETTINGS.x1
        template.ylabel2.x = self.PLOT_SETTINGS.x2
        template.ylabel1.texttable = self.PLOT_SETTINGS.tictable
        template.ylabel2.texttable = self.PLOT_SETTINGS.tictable
        template.ylabel1.textorientation = \
            self.PLOT_SETTINGS.yticorientation
        template.ylabel2.textorientation = \
            self.PLOT_SETTINGS.yticorientation

        if self.PLOT_SETTINGS.xtic1.y1 is not None:
            template.xtic1.y1 = self.PLOT_SETTINGS.xtic1.y1
            template.xtic1.priority = 1
        if self.PLOT_SETTINGS.xtic1.y2 is not None:
            template.xtic1.y2 = self.PLOT_SETTINGS.xtic1.y2
            template.xtic1.priority = 1
        if self.PLOT_SETTINGS.xtic2.y1 is not None:
            template.xtic2.y1 = self.PLOT_SETTINGS.xtic2.y1
            template.xtic2.priority = 1
        if self.PLOT_SETTINGS.xtic2.y2 is not None:
            template.xtic2.y2 = self.PLOT_SETTINGS.xtic2.y2
            template.xtic2.priority = 1
        if self.PLOT_SETTINGS.ytic1.x1 is not None:
            template.ytic1.x1 = self.PLOT_SETTINGS.ytic1.x1
            template.ytic1.priority = 1
        if self.PLOT_SETTINGS.ytic1.x2 is not None:
            template.ytic1.x2 = self.PLOT_SETTINGS.ytic1.x2
            template.ytic1.priority = 1
        if self.PLOT_SETTINGS.ytic2.x1 is not None:
            template.ytic2.priority = 1
            template.ytic2.x1 = self.PLOT_SETTINGS.ytic2.x1
        if self.PLOT_SETTINGS.ytic2.x2 is not None:
            template.ytic2.priority = 1
            template.ytic2.x2 = self.PLOT_SETTINGS.ytic2.x2
        template.legend.x1 = self.PLOT_SETTINGS.legend.x1
        template.legend.x2 = self.PLOT_SETTINGS.legend.x2
        template.legend.y1 = self.PLOT_SETTINGS.legend.y1
        template.legend.y2 = self.PLOT_SETTINGS.legend.y2
        try:
            tmp = vcs.createtextorientation('crap22')
        except Exception:
            tmp = vcs.gettextorientation('crap22')
        tmp.height = 12
        # tmp.halign = 'center'
        # template.legend.texttable = tmp
        template.legend.textorientation = tmp
        return template

    def _repr_png_(self):
        import tempfile
        tmp = tempfile.mktemp() + ".png"
        self.x.png(tmp)
        f = open(tmp, "rb")
        st = f.read()
        f.close()
        return st

    def plot(self, data=None, mesh=None, template=None,
             meshfill=None, x=None, bg=0, multiple=1.1):
        self.bg = bg
        # Create the vcs canvas
        if x is not None:
            self.x = x

        # Continents bug
        # x.setcontinentstype(0)
        # gets the thing to plot !
        if data is None:
            data = self.get()

        # Do we use a predefined template ?
        if template is None:
            template = self.generateTemplate()
        else:
            if isinstance(template, vcs.template.P):
                tid = template.name
            elif isinstance(template, str):
                tid = template
            else:
                raise 'Error cannot understand what you mean by template=' + \
                    str(template)

            template = vcs.createtemplate(source=tid)

        # Do we use a predefined meshfill ?
        if meshfill is None:
            mtics = {}
            for i in range(100):
                mtics[i - .5] = ''
            meshfill = vcs.createmeshfill()
            meshfill.xticlabels1 = eval(data.getAxis(1).names)
            meshfill.yticlabels1 = eval(data.getAxis(0).names)

            meshfill.datawc_x1 = -.5
            meshfill.datawc_x2 = data.shape[1] - .5
            meshfill.datawc_y1 = -.5
            meshfill.datawc_y2 = data.shape[0] - .5
            meshfill.mesh = self.PLOT_SETTINGS.draw_mesh
            meshfill.missing = self.PLOT_SETTINGS.missing_color
            meshfill.xticlabels2 = mtics
            meshfill.yticlabels2 = mtics
            if self.PLOT_SETTINGS.colormap is None:
                self.set_colormap()
            elif self.x.getcolormapname() != self.PLOT_SETTINGS.colormap:
                self.x.setcolormap(self.PLOT_SETTINGS.colormap)

            if self.PLOT_SETTINGS.levels is None:
                min, max = vcs.minmax(data)
                if max != 0:
                    max = max + .000001
                levs = vcs.mkscale(min, max)
            else:
                levs = self.PLOT_SETTINGS.levels

            if len(levs) > 1:
                meshfill.levels = levs
                if self.PLOT_SETTINGS.fillareacolors is None:
                    if self.PLOT_SETTINGS.colormap is None:
                        # Default colormap only use range 16->40
                        cols = vcs.getcolors(levs, list(range(144, 156)), split=1)
                    else:
                        cols = vcs.getcolors(levs, split=1)
                    meshfill.fillareacolors = cols
                else:
                    meshfill.fillareacolors = self.PLOT_SETTINGS.fillareacolors

            # Now creates the mesh associated
            n = int(multiple)
            ntot = int((multiple - n) * 10 + .1)
            sh = list(data.shape)
            sh.append(2)
            Indx = MV2.indices((sh[0], sh[1]))
            Y = Indx[0]
            X = Indx[1]

            if ntot == 1:
                sh.append(4)
                M = MV2.zeros(sh)
                M[:, :, 0, 0] = Y - .5
                M[:, :, 1, 0] = X - .5
                M[:, :, 0, 1] = Y - .5
                M[:, :, 1, 1] = X + .5
                M[:, :, 0, 2] = Y + .5
                M[:, :, 1, 2] = X + .5
                M[:, :, 0, 3] = Y + .5
                M[:, :, 1, 3] = X - .5
                M = MV2.reshape(M, (sh[0] * sh[1], 2, 4))
            elif ntot == 2:
                sh.append(3)
                M = MV2.zeros(sh)
                M[:, :, 0, 0] = Y - .5
                M[:, :, 1, 0] = X - .5
                M[:, :, 0, 1] = Y + .5 - (n - 1)
                M[:, :, 1, 1] = X - 0.5 + (n - 1)
                M[:, :, 0, 2] = Y + .5
                M[:, :, 1, 2] = X + .5
                M = MV2.reshape(M, (sh[0] * sh[1], 2, 3))
            elif ntot == 3:
                design = int((multiple - n) * 100 + .1)
                if design == 33:
                    sh.append(3)
                    M = MV2.zeros(sh)
                    if n == 1:
                        M[:, :, 0, 0] = Y - .5
                        M[:, :, 1, 0] = X - .5
                        M[:, :, 0, 1] = Y + .5
                        M[:, :, 1, 1] = X
                        M[:, :, 0, 2] = Y + .5
                        M[:, :, 1, 2] = X - .5
                    elif n == 2:
                        M[:, :, 0, 0] = Y - .5
                        M[:, :, 1, 0] = X - .5
                        M[:, :, 0, 1] = Y + .5
                        M[:, :, 1, 1] = X
                        M[:, :, 0, 2] = Y - .5
                        M[:, :, 1, 2] = X + .5
                    elif n == 3:
                        M[:, :, 0, 0] = Y + .5
                        M[:, :, 1, 0] = X + .5
                        M[:, :, 0, 1] = Y + .5
                        M[:, :, 1, 1] = X
                        M[:, :, 0, 2] = Y - .5
                        M[:, :, 1, 2] = X + .5
                    M = MV2.reshape(M, (sh[0] * sh[1], 2, 3))
                elif design == 32:
                    sh.append(5)
                    M = MV2.zeros(sh)
                    M[:, :, 0, 0] = Y
                    M[:, :, 1, 0] = X
                    d = .5 / MV2.sqrt(3.)
                    if n == 1:
                        M[:, :, 0, 1] = Y + .5
                        M[:, :, 1, 1] = X
                        M[:, :, 0, 2] = Y + .5
                        M[:, :, 1, 2] = X - .5
                        M[:, :, 0, 3] = Y - d
                        M[:, :, 1, 3] = X - .5
                        # dummy point for n==1 or 3
                        M[:, :, 0, 4] = Y
                        M[:, :, 1, 4] = X
                    if n == 2:
                        M[:, :, 0, 1] = Y - d
                        M[:, :, 1, 1] = X - .5
                        M[:, :, 0, 2] = Y - .5
                        M[:, :, 1, 2] = X - .5
                        M[:, :, 0, 3] = Y - .5
                        M[:, :, 1, 3] = X + .5
                        M[:, :, 0, 4] = Y - d
                        M[:, :, 1, 4] = X + .5
                    elif n == 3:
                        M[:, :, 0, 1] = Y + .5
                        M[:, :, 1, 1] = X
                        M[:, :, 0, 2] = Y + .5
                        M[:, :, 1, 2] = X + .5
                        M[:, :, 0, 3] = Y - d
                        M[:, :, 1, 3] = X + .5
                        # dummy point for n==1 or 3
                        M[:, :, 0, 4] = Y
                        M[:, :, 1, 4] = X
                    M = MV2.reshape(M, (sh[0] * sh[1], 2, 5))
                else:
                    sh.append(5)
                    M = MV2.zeros(sh)
                    M[:, :, 0, 0] = Y
                    M[:, :, 1, 0] = X
                    d = 1. / 3.
                    if n == 1:
                        M[:, :, 0, 1] = Y + .5
                        M[:, :, 1, 1] = X
                        M[:, :, 0, 2] = Y + .5
                        M[:, :, 1, 2] = X - .5
                        M[:, :, 0, 3] = Y - d

                        M[:, :, 1, 3] = X - .5
                        # dummy point for n==1 or 3
                        M[:, :, 0, 4] = Y
                        M[:, :, 1, 4] = X
                    if n == 2:
                        M[:, :, 0, 1] = Y - d
                        M[:, :, 1, 1] = X - .5
                        M[:, :, 0, 2] = Y - .5
                        M[:, :, 1, 2] = X - .5
                        M[:, :, 0, 3] = Y - .5
                        M[:, :, 1, 3] = X + .5
                        M[:, :, 0, 4] = Y - d
                        M[:, :, 1, 4] = X + .5
                    elif n == 3:
                        M[:, :, 0, 1] = Y + .5
                        M[:, :, 1, 1] = X
                        M[:, :, 0, 2] = Y + .5
                        M[:, :, 1, 2] = X + .5
                        M[:, :, 0, 3] = Y - d
                        M[:, :, 1, 3] = X + .5
                        # dummy point for n==1 or 3
                        M[:, :, 0, 4] = Y
                        M[:, :, 1, 4] = X
                    M = MV2.reshape(M, (sh[0] * sh[1], 2, 5))
            elif ntot == 4:
                sh.append(3)
                M = MV2.zeros(sh)
                M[:, :, 0, 0] = Y
                M[:, :, 1, 0] = X
                if n == 1:
                    M[:, :, 0, 1] = Y + .5
                    M[:, :, 1, 1] = X + .5
                    M[:, :, 0, 2] = Y + .5
                    M[:, :, 1, 2] = X - .5
                elif n == 2:
                    M[:, :, 0, 1] = Y + .5
                    M[:, :, 1, 1] = X - .5
                    M[:, :, 0, 2] = Y - .5
                    M[:, :, 1, 2] = X - .5
                elif n == 3:
                    M[:, :, 0, 1] = Y - .5
                    M[:, :, 1, 1] = X - .5
                    M[:, :, 0, 2] = Y - .5
                    M[:, :, 1, 2] = X + .5
                elif n == 4:
                    M[:, :, 0, 1] = Y - .5
                    M[:, :, 1, 1] = X + .5
                    M[:, :, 0, 2] = Y + .5
                    M[:, :, 1, 2] = X + .5
                M = MV2.reshape(M, (sh[0] * sh[1], 2, 3))
            else:
                raise RuntimeError("Portrait plot support only up to 4 subcells at the moment")
        else:
            if isinstance(meshfill, vcs.meshfill.P):
                tid = mesh.id
            elif isinstance(meshfill, str):
                tid = mesh
            else:
                raise 'Error cannot understand what you mean by meshfill=' + \
                    str(meshfill)
            meshfill = vcs.createmeshfill(source=tid)

        if mesh is None:
            mesh = M

        raveled = MV2.ravel(data)
        self.x.plot(raveled, mesh, template, meshfill, bg=self.bg, continents=0)

        # If required plot values
        if self.PLOT_SETTINGS.values.show:
            self.draw_values(raveled, mesh, meshfill, template)

        # Now prints the rest of the title, etc...
        # but only if n==1
        if n == 1:
            axes_param = []
            for a in data.getAxis(0).id.split('___'):
                axes_param.append(a)
            for a in data.getAxis(1).id.split('___'):
                axes_param.append(a)
            nparam = 0
            for p in self.parameters_list:
                if p not in self.dummies and \
                        p not in self.auto_dummies and \
                        p not in axes_param:
                    nparam += 1

            if self.verbose:
                print('NPARAM:', nparam)
            if nparam > 0:
                for i in range(nparam):
                    j = MV2.ceil(float(nparam) / (i + 1.))
                    if j <= i:
                        break
                npc = i  # number of lines
                npl = int(j)  # number of coulmns
                if npc * npl < nparam:
                    npl += 1
                # computes space between each line
                dl = (.95 - template.data.y2) / npl
                dc = .9 / npc
                npci = 0  # counter for columns
                npli = 0  # counter for lines
                for p in self.parameters_list:
                    if p not in self.dummies and \
                            p not in self.auto_dummies and \
                            p not in axes_param:
                        txt = self.x.createtext(
                            None,
                            self.PLOT_SETTINGS.parametertable.name,
                            None,
                            self.PLOT_SETTINGS.parameterorientation.name)
                        value = getattr(self, p)
                        if (isinstance(value, (list, tuple)) and
                                len(value) == 1):
                            txt.string = p + ':' + \
                                str(self.makestring(p, value[0]))
                            display = 1
                        elif isinstance(value, (str, int, float)):
                            txt.string = p + ':' + \
                                str(self.makestring(p, value))
                            display = 1
                        else:
                            display = 0

                        if display:
                            # Now figures out where to put these...
                            txt.x = [(npci) * dc + dc / 2. + .05]
                            txt.y = [1. - (npli) * dl - dl / 2.]
                            npci += 1
                            if npci >= npc:
                                npci = 0
                                npli += 1
                            if p in list(self.altered.keys()):
                                dic = self.altered[p]
                                if dic['size'] is not None:
                                    txt.size = dic['size']
                                if dic['color'] is not None:
                                    txt.color = dic['color']
                                if dic['x'] is not None:
                                    txt.x = dic['x']
                                if dic['y'] is not None:
                                    txt.y = dic['y']
                            self.x.plot(txt, bg=self.bg, continents=0)
            if self.PLOT_SETTINGS.time_stamp is not None:
                sp = time.ctime().split()
                sp = sp[:3] + [sp[-1]]
                self.PLOT_SETTINGS.time_stamp.string = ''.join(sp)
                self.x.plot(
                    self.PLOT_SETTINGS.time_stamp,
                    bg=self.bg,
                    continents=0)
            if self.PLOT_SETTINGS.logo is not None:
                self.PLOT_SETTINGS.logo.plot(self.x, bg=self.bg)
        return mesh, template, meshfill

    def draw_values(self, raveled, mesh, meshfill, template):
        # Values to use (data or user passed)
        if self.PLOT_SETTINGS.values.array is None:
            data = MV2.array(raveled)
        else:
            data = MV2.ravel(self.PLOT_SETTINGS.values.array)
        if isinstance(raveled, numpy.ma.core.MaskedArray):
            data.mask = data.mask + raveled.mask

        # Now remove masked values
        if data.mask is not numpy.ma.nomask:  # we have missing
            indices = numpy.argwhere(numpy.ma.logical_not(data.mask))
            data = data.take(indices).filled(0)[:, 0]
            M = mesh.filled()[indices][:, 0]
            raveled = raveled.take(indices).filled(0.)[:, 0]
        else:
            M = mesh.filled()

        # Baricenters
        xcenters = numpy.average(M[:, 1], axis=-1)
        ycenters = numpy.average(M[:, 0], axis=-1)
        self.PLOT_SETTINGS.values.text.viewport = [template.data.x1, template.data.x2,
                                                   template.data.y1, template.data.y2]
        if not numpy.allclose(meshfill.datawc_x1, 1.e20):
            self.PLOT_SETTINGS.values.text.worldcoordinate = [meshfill.datawc_x1,
                                                              meshfill.datawc_x2,
                                                              meshfill.datawc_y1,
                                                              meshfill.datawc_y2]
        else:
            self.PLOT_SETTINGS.values.text.worldcoordinate = [M[:, 1].min(),
                                                              M[:, 1].max(),
                                                              M[:, 0].min(),
                                                              M[:, 0].max()]

        self.PLOT_SETTINGS.values.text.string = [
            self.PLOT_SETTINGS.values.format.format(value) for value in data]

        # Now that we have the formatted values we need get the longest string
        lengths = [len(txt) for txt in self.PLOT_SETTINGS.values.text.string]
        longest = max(lengths)
        index = lengths.index(longest)

        tmptxt = vcs.createtext()
        tmptxt.string = self.PLOT_SETTINGS.values.text.string[index]
        tmptxt.x = xcenters[index]
        tmptxt.y = ycenters[index]
        smallY = M[index, 0, :].min()
        bigY = M[index, 0, :].max()
        smallX = M[index, 1, :].min()
        bigX = M[index, 1, :].max()
        tmptxt.worldcoordinate = self.PLOT_SETTINGS.values.text.worldcoordinate
        tmptxt.viewport = self.PLOT_SETTINGS.values.text.viewport
        # Now try to shrink until it fits
        extent = self.x.gettextextent(tmptxt)[0]
        while ((extent[1] - extent[0]) / (bigX - smallX) > 1.01 or
               (extent[3] - extent[2]) / (bigY - smallY) > 1.01) and \
                tmptxt.height >= 1:
            tmptxt.height -= 1
            extent = self.x.gettextextent(tmptxt)[0]
        self.PLOT_SETTINGS.values.text.height = tmptxt.height

        # Finally we need to split into two text objects for dark and light background
        # Step 1: figure out each bin color type (dark/light)
        colormap = self.x.colormap
        if colormap is None:
            colormap = vcs._colorMap
        cmap = vcs.getcolormap(colormap)
        colors = meshfill.fillareacolors
        dark_bins = [
            is_dark_color_type(
                *cmap.getcolorcell(color)) for color in colors]

        # Step 2: put values into bin (color where they land)
        bins = meshfill.levels[1:-1]
        binned = numpy.digitize(raveled, bins)
        isdark = [dark_bins[indx] for indx in binned]
        tmptxt = vcs.createtext(
            Tt_source=self.PLOT_SETTINGS.values.text.Tt_name,
            To_source=self.PLOT_SETTINGS.values.text.To_name)
        for pick, color in [(numpy.argwhere(isdark), self.PLOT_SETTINGS.values.lightcolor),
                            (numpy.argwhere(numpy.logical_not(isdark)), self.PLOT_SETTINGS.values.darkcolor)]:
            tmptxt.x = xcenters.take(pick)[:, 0].tolist()
            tmptxt.y = ycenters.take(pick)[:, 0].tolist()
            tmptxt.string = numpy.array(
                self.PLOT_SETTINGS.values.text.string).take(pick)[
                :, 0].tolist()
            tmptxt.color = color
            self.x.plot(tmptxt, bg=self.bg, continents=0)

    def set_colormap(self):
        self.x.setcolormap("bl_rd_12")
