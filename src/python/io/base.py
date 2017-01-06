import json
import cdms2
import MV2
import cdutil
import genutil
import os
import pcmdi_metrics
import cdat_info
import hashlib
import subprocess
import numpy
import collections
import sys
import shlex
import datetime

value = 0
cdms2.setNetcdfShuffleFlag(value)  # where value is either 0 or 1
cdms2.setNetcdfDeflateFlag(value)  # where value is either 0 or 1
# where value is a integer between 0 and 9 included
cdms2.setNetcdfDeflateLevelFlag(value)

# cdutil region object need a serializer

# Platform

def populate_prov(prov,cmd,pairs,sep=None,index=1,fill_missing=False):
    try:
        p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        return
    out,stde = p.communicate()
    if stde != '':
        return
    for strBit in out.splitlines():
        for key, value in pairs.iteritems():
            if value in strBit:
                prov[key] = strBit.split(sep)[index].strip()
    if fill_missing is not False:
        for k in pairs:
            if not prov.has_key(k):
                prov[k] = fill_missing
    return

def generateProvenance():
    prov = collections.OrderedDict()
    platform = os.uname()
    platfrm = collections.OrderedDict()
    platfrm["OS"] = platform[0]
    platfrm["Version"]= platform[2]
    platfrm["Name"] =  platform[1]
    prov["platform"] = platfrm
    try:
        logname = os.getlogin()
    except:
        try:
            import pwd
            logname = pwd.getpwuid(os.getuid())[0]
        except:
            try: 
                logname = os.environ.get('LOGNAME', 'unknown')
            except:
                logger.exception('Couldn\'t determine a login name for provenance information')
                logname = 'unknown-loginname'
    prov["userId"] = logname
    prov["osAccess"] = bool(os.access('/', os.W_OK) * os.access('/', os.R_OK))
    prov["commandLine"] = " ".join(sys.argv)
    prov["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prov["conda"]=collections.OrderedDict()
    pairs = {
             'Platform':'platform ',
             'Version':'conda version ',
             'IsPrivate':'conda is private ',
             'envVersion':'conda-env version ',
             'buildVersion':'conda-build version ',
             'PythonVersion':'python version ',
             'RootEnvironment':'root environment ',
             'DefaultEnvironment':'default environment '
             }
    populate_prov(prov["conda"],"conda info",pairs,sep=":",index=-1)
    pairs = {
             'CDP':'cdp ',
             'cdms':'cdms2 ',
             'cdtime':'cdtime ',
             'cdutil':'cdutil ',
             'esmf':'esmf ',
             'genutil':'genutil ',
             'matplotlib':'matplotlib ',
             'numpy':'numpy ',
             'python':'python ',
             'vcs':'vcs ',
             'vtk':'vtk-cdat ',
             'vcs':'vcs-nox ',
             'vtk':'vtk-cdat-nox ',
             }
    prov["packages"]=collections.OrderedDict()
    populate_prov(prov["packages"],"conda list",pairs,fill_missing=None) 
    pairs = {
             'PMP':'pcmdi_metrics',
             'PMPObs':'pcmdi_metrics_obs',
             }
    populate_prov(prov["packages"],"conda list",pairs,fill_missing=None) 
    # TRying to capture glxinfo

    pairs = {
            "vendor" : "OpenGL vendor string",
            "renderer": "OpenGL renderer string",
            "version" : "OpenGL version string",
            "shading language version": "OpenGL shading language version string",
            }

    prov["openGL"]=collections.OrderedDict()
    populate_prov(prov["openGL"],"glxinfo",pairs,sep=":",index=-1)
    prov["openGL"]["GLX"]={"server":collections.OrderedDict(),"client":collections.OrderedDict()}
    pairs = {
            "version" : "GLX version",
            }

    populate_prov(prov["openGL"]["GLX"],"glxinfo",pairs,sep=":",index=-1)
    pairs = {
            "vendor" :"server glx vendor string",
            "version" : "server glx version string",
            }

    populate_prov(prov["openGL"]["GLX"]["server"],"glxinfo",pairs,sep=":",index=-1)
    pairs = {
            "vendor": "client glx vendor string",
            "version": "client glx version string",
            }

    populate_prov(prov["openGL"]["GLX"]["client"],"glxinfo",pairs,sep=":",index=-1)

    return prov

def update_dict(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update_dict(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


class CDMSDomainsEncoder(json.JSONEncoder):

    def default(self, o):
        cmp = o.components()[0].kargs
        args = ",".join(["%s=%s" % (k, v) for k, v in cmp.iteritems()])
        return {o.id: "cdutil.region.domain(%s)" % args}


class Base(genutil.StringConstructor):

    def __init__(self, root, file_template, file_mask_template=None):
        genutil.StringConstructor.__init__(self, root + "/" + file_template)
        self.targetGrid = None
        self.mask = None
        self.targetMask = None
        self.file_mask_template = file_mask_template
        self.root = root

    def __call__(self):
        return os.path.abspath(genutil.StringConstructor.__call__(self))

    def get(self, var, varInFile=None, region={}, *args, **kargs):
        if region is None:
            region = {}

        self.variable = var
        if varInFile is None:
            varInFile = var
        # First extract data
        f = cdms2.open(os.path.abspath(self()))
        out = f(varInFile, *args, **kargs)
        f.close()

        # Now are we masking anything?
        value = region.get("value", None)
        if value is not None:  # Indeed we are
            if self.mask is None:
                if isinstance(self.file_mask_template, basestring):
                    self.file_mask_template = Base(
                        self.root, self.file_mask_template, {
                            "domain": region.get(
                                "domain", None)})
                try:
                    oMask = self.file_mask_template.get("sftlf")
                # ok that failed falling back on autogenerate
                except:
                    oMask = cdutil.generateLandSeaMask(
                        out,
                        regridTool=self.regridTool).filled(1.) * 100.
                    oMask = MV2.array(oMask)
                    oMask.setAxis(-1, out.getLongitude())
                    oMask.setAxis(-2, out.getLatitude())
                self.mask = oMask
            if self.mask.shape != out.shape:
                dum, msk = genutil.grower(out, self.mask)
            else:
                msk = self.mask
            msk = MV2.not_equal(msk, value)
            out = MV2.masked_where(msk, out)
        if self.targetGrid is not None:
            out = out.regrid(
                self.targetGrid,
                regridTool=self.regridTool,
                regridMethod=self.regridMethod,
                coordSys='deg',
                diag={},
                periodicity=1)
            if self.targetMask is not None:
                if self.targetMask.shape != out.shape:
                    dum, msk = genutil.grower(out, self.targetMask)
                else:
                    msk = self.targetMask
                out = MV2.masked_where(msk, out)
        # Now are we looking at a region in particular?
        domain = region.get("domain", None)
        if domain is not None:  # Ok we are subsetting
            if isinstance(domain, dict):
                out = out(**domain)
            elif isinstance(domain, (list, tuple)):
                out = out(*domain)
            elif isinstance(domain, cdms2.selectors.Selector):
                domain.id = region.get("id", "region")
                out = out(*[domain])
        return out


    def setTargetGrid(self, target, regridTool="esmf", regridMethod="linear"):
        self.regridTool = regridTool
        self.regridMethod = regridMethod
        if target == "2.5x2.5":
            self.targetGrid = cdms2.createUniformGrid(
                -88.875,
                72,
                2.5,
                0,
                144,
                2.5)
            self.targetGridName = target
        elif cdms2.isGrid(target):
            self.targetGrid = target
            self.targetGridName = target
        else:
            raise RuntimeError("Unknown grid: %s" % target)

    def write(self, data, type="json", mode="w", *args, **kargs):
        fnm = os.path.abspath(self()) + ".%s" % type
        try:
            os.makedirs(os.path.split(fnm)[0])
        except:
            pass
        if not os.path.exists(os.path.split(fnm)[0]):
            raise RuntimeError(
                "Could not create output directory: %s" %
                (os.path.split(fnm)[0]))
        if type.lower() == "json":
            json_version = float(kargs.get("json_version", data.get("json_version", 3.0)))
            json_structure = kargs.get("json_structure", data.get("json_structure", None))
            if json_version >= 3. and json_structure is None:
                raise Exception(
                    "json_version 3.0 of PMP requires json_structure to be passed" +
                    "to the write function or part of the dictionary dumped")
            for k in ["json_structure", "json_version"]:
                if k in kargs:
                    del(kargs[k])
            data["json_version"] = json_version
            data["json_structure"] = json_structure
            f = open(fnm, mode)
            data["provenance"] = generateProvenance()
            json.dump(data, f, cls=CDMSDomainsEncoder, *args, **kargs)
            f.close()
            print "Results saved to JSON file:", fnm
        elif type.lower() in ["asc", "ascii", "txt"]:
            f = open(fnm, mode)
            for k in data.keys():
                f.write("%s  %s \n" % (k, data[k]))
            f.close()
        elif type.lower() == "nc":
            f = cdms2.open(fnm, mode)
            f.write(data, *args, **kargs)
            f.metrics_git_sha1 = pcmdi_metrics.__git_sha1__
            f.uvcdat_version = cdat_info.get_version()
            f.close()
        else:
            raise RuntimeError("Unknown type: %s" % type)

    def hash(self, blocksize=65536):
        afile = open(self())
        buf = afile.read(blocksize)
        hasher = hashlib.md5()
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
        afile.close()
        return hasher.hexdigest()


class JSONs(object):

    def addDict2Self(self, json_dict, json_struct, json_version):
        if float(json_version) == 1.0:
            V = json_dict[json_dict.keys()[0]]
            for model in V.keys():  # loop through models
                m = V[model]
                # print "FIRST M:",m.keys()
                for ref in m.keys():
                    aref = m[ref]
                    if not(isinstance(aref, dict) and "source" in aref):  # not an obs key
                        continue
                    # print "\treading in ref:",ref
                    # print aref.keys()
                    reals = aref.keys()
                    src = reals.pop(reals.index("source"))
                    for real in reals:
                        # print "\t\treading in realization:",real
                        # print real
                        areal = aref[real]
                        areal2 = {"source": src}
                        for region in areal.keys():
                            # print "\t\t\tREGION:",region
                            reg = areal[region]
                            if region == "global":
                                region2 = ""
                            else:
                                region2 = region + "_"
                            areal2[region2 + "global"] = {}
                            areal2[region2 + "NHEX"] = {}
                            areal2[region2 + "SHEX"] = {}
                            areal2[region2 + "TROPICS"] = {}
                            # print "OK HERE REGIONS:",areal2.keys()
                            key_stats = reg.keys()
                            for k in key_stats:
                                if k[:7] == "custom_":
                                    continue
                                else:
                                    sp = k.split("_")
                                    new_key = "_".join(sp[:-1])
                                    domain = sp[-1]
                                    if domain == "GLB":
                                        domain = "global"
                                    sp = new_key.split("_")
                                    stat = "_".join(sp[:-1])
                                    stat_dict = areal2[region2 + domain].get(stat, {})
                                    season = sp[-1]
                                    season_dict = stat_dict
                                    stat_dict[season] = reg[k]
                                    if stat in areal2[region2 + domain]:
                                        areal2[region2 + domain][stat].update(stat_dict)
                                    else:
                                        areal2[region2 + domain][stat] = stat_dict
                        # Now we can replace the realization with the correctly formatted one
                        # print "AREAL@:",areal2
                        aref[real] = areal2
                    # restore ref into model
                    m[ref] = aref
        elif float(json_version) == 2.0:
            V = json_dict[json_dict.keys()[0]]
            for model in V.keys():  # loop through models
                m = V[model]
                for ref in m.keys():
                    aref = m[ref]
                    if not(isinstance(aref, dict) and "source" in aref):  # not an obs key
                        continue
                    # print "\treading in ref:",ref
                    # print aref.keys()
                    reals = aref.keys()
                    src = reals.pop(reals.index("source"))
                    for real in reals:
                        # print "\t\treading in realization:",real
                        # print real
                        areal = aref[real]
                        for region in areal.keys():
                            reg = areal[region]
                            key_stats = reg.keys()
                            for k in key_stats:
                                if k[:7] == "custom_":
                                    continue
                                sp = k.split("_")
                                season = sp[-1]
                                stat = "_".join(sp[:-1])
                                stat_dict = reg.get(stat, {})
                                season_dict = stat_dict.get(season, {})
                                season_dict[season] = reg[k]
                                # if stat_dict.has_key(stat):
                                #    stat_dict[stat].update(season_dict)
                                # else:
                                #    stat_dict[stat]=season_dict
                                del(reg[k])
                                if stat in reg:
                                    reg[stat].update(season_dict)
                                else:
                                    reg[stat] = season_dict
                        aref[real] = areal
                    # restore ref into model
                    m[ref] = aref
                V[model] = m
            json_dict[json_dict.keys()[0]] = V
        update_dict(self.data, json_dict)

    def get_axes_values_recursive(self, depth, max_depth, data, values):
        for k in data.keys():
            if k not in self.ignored_keys and (isinstance(data[k], dict) or depth == max_depth):
                values[depth].add(k)
                if depth != max_depth:
                    self.get_axes_values_recursive(depth + 1, max_depth, data[k], values)

    def get_array_values_from_dict_recursive(self, out, ids, nms, axval, axes):
        if len(axes) > 0:
            for i, val in enumerate(axes[0][:]):
                self.get_array_values_from_dict_recursive(out, list(ids) +
                                                          [i, ], list(nms) +
                                                          [axes[0].id], list(axval) +
                                                          [val, ], axes[1:])
        else:
            vals = self.data
            for k in axval:
                try:
                    vals = vals[k]
                except:
                    vals = 1.e20
            try:
                out[tuple(ids)] = float(vals)
            except:
                out[tuple(ids)] = 1.e20

    def __init__(self, files=[], structure=[], ignored_keys=[], oneVariablePerFile=True):
        self.json_version = 3.0
        self.json_struct = structure
        self.data = {}
        self.axes = None
        self.ignored_keys = ignored_keys
        self.oneVariablePerFile = oneVariablePerFile
        if len(files) == 0:
            raise Exception("You need to pass at least one file")

        for fnm in files:
            self.addJson(fnm)

    def addJson(self, filename):
        f = open(filename)
        tmp_dict = json.load(f)
        json_struct = tmp_dict.get("json_structure", list(self.json_struct))
        json_version = tmp_dict.get("json_version", self.json_version)
        if self.oneVariablePerFile and json_struct[0] == "variable":
            json_struct = json_struct[1:]
        if self.oneVariablePerFile and json_struct[0] != "variable":
            json_struct.insert(0, "variable")
            var = tmp_dict.get("Variable", None)
            if var is None:  # Not stored in json, need to get from file name
                fnm = os.path.basename(filename)
                varnm = fnm.split("_")[0]
            else:
                varnm = var["id"]
                if "level" in var:
                    varnm += "-%i" % int(var["level"] / 100.)
            tmp_dict = {varnm: tmp_dict["RESULTS"]}
        else:
            tmp_dict = tmp_dict["RESULTS"]
        self.addDict2Self(tmp_dict, json_struct, json_version)

    def getAxis(self, axis):
        axes = self.getAxisList()
        for a in axes:
            if a.id == axis:
                return a
        return None

    def getAxisList(self, use_cache=True):
        if use_cache and self.axes is not None:
            return self.axes
        values = []
        axes = []
        for a in self.json_struct:
            values.append(set())
        self.get_axes_values_recursive(0, len(self.json_struct) - 1, self.data, values)
        for i, nm in enumerate(self.json_struct):
            axes.append(cdms2.createAxis(sorted(list(values[i])), id=nm))
        self.axes = axes
        return self.axes

    def __call__(self, **kargs):
        """ Returns the array of values"""
        axes = self.getAxisList()
        sh = []
        ids = []
        for a in axes:
            sh.append(len(a))  # store length to construct array shape
            ids.append(a.id)  # store ids

        # first let's see which vars are actually asked for
        # for now assume all keys means restriction on dims
        for axis_id in kargs:
            if axis_id not in ids:
                raise ValueError("Invalid axis '%s'" % axis_id)
            index = ids.index(axis_id)
            value = kargs[axis_id]
            if isinstance(value, basestring):
                value = [value]
            if not isinstance(value, (list, tuple, slice)):
                raise TypeError(
                    "Invalid subsetting type for axis '%s', axes can only be subsetted by string,list or slice" %
                    axis_id)
            if isinstance(value, slice):
                axes[index] = axes[index].subAxis(
                    value.start, value.stop, value.step)
                sh[index] = len(axes[index])
            else:  # ok it's a list
                for v in value:
                    if v not in axes[index][:]:
                        raise ValueError(
                            "Unkwown value '%s' for axis '%s'" %
                            (v, axis_id))
                axis = cdms2.createAxis(value, id=axes[index].id)
                axes[index] = axis
                sh[index] = len(axis)

        array = numpy.ma.ones(sh, dtype=numpy.float)
        # Now let's fill this array
        self.get_array_values_from_dict_recursive(array, [], [], [], axes)

        array = MV2.masked_greater(array, 9.e19)
        array.id = "pmp"
        array.setAxisList(axes)
        return array
