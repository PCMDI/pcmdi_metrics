import os
import logging
import json
import genutil
import cdat_info
import cdutil
import MV2
import cdms2
import hashlib
import numpy
import collections
import pcmdi_metrics
import cdp.cdp_io
import subprocess
import sys
import shlex
import datetime
from pcmdi_metrics import LOG_LEVEL


value = 0
cdms2.setNetcdfShuffleFlag(value)  # where value is either 0 or 1
cdms2.setNetcdfDeflateFlag(value)  # where value is either 0 or 1
# where value is a integer between 0 and 9 included
cdms2.setNetcdfDeflateLevelFlag(value)
logging.basicConfig(level=LOG_LEVEL)


# cdutil region object need a serializer
def update_dict(d, u, overwriteOnDuplicate=True):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update_dict(d.get(k, {}), v)
            if overwriteOnDuplicate is True:
                d[k]=r
	    else:
		tmp = {k:r}
		update_dict_no_overwrite(d,tmp,level=level)
        else:
            d[k] = v
    return d


def update_dict_no_overwrite(d,u,level=0):
    for k,v in u.items():
        if k in d and level==0:
            i=1
            while str(k)+"_%i" % i in d:
                i+=1
            d[str(k)+"_%i"%i] = v 
        else:
            if isinstance(v,dict) and k in d:
                d[k] = update_dict_no_overwrite(d[k],v,level-1)
            else:   
                d[k] = v
    return d    

# Platform
def populate_prov(prov, cmd, pairs, sep=None, index=1, fill_missing=False):
    try:
        p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        return
    out, stde = p.communicate()
    if stde != '':
        return
    for strBit in out.splitlines():
        for key, value in pairs.iteritems():
            if value in strBit:
                prov[key] = strBit.split(sep)[index].strip()
    if fill_missing is not False:
        for k in pairs:
            if k not in prov:
                prov[k] = fill_missing
    return


def generateProvenance():
    prov = collections.OrderedDict()
    platform = os.uname()
    platfrm = collections.OrderedDict()
    platfrm["OS"] = platform[0]
    platfrm["Version"] = platform[2]
    platfrm["Name"] = platform[1]
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
                logname = 'unknown-loginname'
    prov["userId"] = logname
    prov["osAccess"] = bool(os.access('/', os.W_OK) * os.access('/', os.R_OK))
    prov["commandLine"] = " ".join(sys.argv)
    prov["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prov["conda"] = collections.OrderedDict()
    pairs = {
        'Platform': 'platform ',
        'Version': 'conda version ',
        'IsPrivate': 'conda is private ',
        'envVersion': 'conda-env version ',
        'buildVersion': 'conda-build version ',
        'PythonVersion': 'python version ',
        'RootEnvironment': 'root environment ',
        'DefaultEnvironment': 'default environment '
    }
    populate_prov(prov["conda"], "conda info", pairs, sep=":", index=-1)
    pairs = {
        'CDP': 'cdp ',
        'cdms': 'cdms2 ',
        'cdtime': 'cdtime ',
        'cdutil': 'cdutil ',
        'esmf': 'esmf ',
        'genutil': 'genutil ',
        'matplotlib': 'matplotlib ',
        'numpy': 'numpy ',
        'python': 'python ',
        'vcs': 'vcs ',
        'vtk': 'vtk-cdat ',
    }
    prov["packages"] = collections.OrderedDict()
    populate_prov(prov["packages"], "conda list", pairs, fill_missing=None)
    pairs = {
        'vcs': 'vcs-nox ',
        'vtk': 'vtk-cdat-nox ',
    }
    populate_prov(prov["packages"], "conda list", pairs, fill_missing=None)
    pairs = {
        'PMP': 'pcmdi_metrics',
        'PMPObs': 'pcmdi_metrics_obs',
    }
    populate_prov(prov["packages"], "conda list", pairs, fill_missing=None)
    # TRying to capture glxinfo
    pairs = {
        "vendor": "OpenGL vendor string",
        "renderer": "OpenGL renderer string",
        "version": "OpenGL version string",
        "shading language version": "OpenGL shading language version string",
    }
    prov["openGL"] = collections.OrderedDict()
    populate_prov(prov["openGL"], "glxinfo", pairs, sep=":", index=-1)
    prov["openGL"]["GLX"] = {"server": collections.OrderedDict(), "client": collections.OrderedDict()}
    pairs = {
        "version": "GLX version",
    }
    populate_prov(prov["openGL"]["GLX"], "glxinfo", pairs, sep=":", index=-1)
    pairs = {
        "vendor": "server glx vendor string",
        "version": "server glx version string",
    }
    populate_prov(prov["openGL"]["GLX"]["server"], "glxinfo", pairs, sep=":", index=-1)
    pairs = {
        "vendor": "client glx vendor string",
        "version": "client glx version string",
    }
    populate_prov(prov["openGL"]["GLX"]["client"], "glxinfo", pairs, sep=":", index=-1)
    return prov


class CDMSDomainsEncoder(json.JSONEncoder):
    def default(self, o):
        components = o.components()[0].kargs
        args = ','.join(
            ['%s=%s' % (key, val) for key, val in components.iteritems()]
        )
        return {o.id: 'cdutil.region.domain(%s)' % args}


class Base(cdp.cdp_io.CDPIO, genutil.StringConstructor):
    def __init__(self, root, file_template, file_mask_template=None):
        genutil.StringConstructor.__init__(self, root + '/' + file_template)
        self.target_grid = None
        self.mask = None
        self.target_mask = None
        self.regrid_tool = 'esmf'
        self.file_mask_template = file_mask_template
        self.root = root
        self.type = ''
        self.setup_cdms2()

    def __call__(self):
        path = os.path.abspath(genutil.StringConstructor.__call__(self))
        if self.type in path:
            return path
        else:
            return path + '.' + self.type

    def read(self):
        pass

    def write(self, data, type='json', *args, **kwargs):
        self.type = type.lower()
        file_name = self()
        dir_path = os.path.split(file_name)[0]

        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except:
                logging.error(
                    'Could not create output directory: %s' % dir_path)

        if self.type == 'json':
            json_version = float(kwargs.get("json_version", data.get("json_version", 3.0)))
            json_structure = kwargs.get("json_structure", data.get("json_structure", None))
            if json_version >= 3.0 and json_structure is None:
                raise Exception(
                    "json_version 3.0 of PMP requires json_structure to be passed" +
                    "to the write function or part of the dictionary dumped")
            for k in ["json_structure", "json_version"]:
                if k in kwargs:
                    del(kwargs[k])
            data["json_version"] = json_version
            data["json_structure"] = json_structure
            f = open(file_name, 'w')
            data["provenance"] = generateProvenance()
            json.dump(data, f, cls=CDMSDomainsEncoder, *args, **kwargs)
            f.close()

        elif self.type in ['asc', 'ascii', 'txt']:
            f = open(file_name, 'w')
            for key in data.keys():
                f.write('%s %s\n' % (key, data[key]))
            f.close()

        elif self.type == 'nc':
            f = cdms2.open(file_name, 'w')
            f.write(data, *args, **kwargs)
            f.metrics_git_sha1 = pcmdi_metrics.__git_sha1__
            f.uvcdat_version = cdat_info.get_version()
            f.close()

        else:
            logging.error('Unknown type: %s' % type)
            raise RuntimeError('Unknown type: %s' % type)

        logging.info('Results saved to a %s file: %s' % (type, file_name))

    def get(self, var, var_in_file=None,
            region={}, *args, **kwargs):
        self.var_from_file = self.extract_var_from_file(
            var, var_in_file, *args, **kwargs)

        self.region = region
        if self.region is None:
            self.region = {}
        self.value = self.region.get('value', None)

        if self.is_masking():
            self.var_from_file = self.mask_var(self.var_from_file)

        self.var_from_file = \
            self.set_target_grid_and_mask_in_var(self.var_from_file)

        self.var_from_file = \
            self.set_domain_in_var(self.var_from_file, self.region)

        return self.var_from_file

    def extract_var_from_file(self, var, var_in_file, *args, **kwargs):
        if var_in_file is None:
            var_in_file = var
        # self.extension = 'nc'
        var_file = cdms2.open(self(), 'r')
        extracted_var = var_file(var_in_file, *args, **kwargs)
        var_file.close()
        return extracted_var

    def is_masking(self):
        if self.value is not None:
            return True
        else:
            return False

    def mask_var(self, var):
        if self.mask is None:
            self.set_file_mask_template()
            self.mask = self.get_mask_from_var(var)
        if self.mask.shape != var.shape:
            dummy, mask = genutil.grower(var, self.mask)
        else:
            mask = self.target_mask
        mask = MV2.not_equal(mask, self.value)
        return MV2.masked_where(mask, var)

    def set_target_grid_and_mask_in_var(self, var):
        if self.target_grid is not None:
            var = var.regrid(self.target_grid, regridTool=self.regrid_tool,
                             regridMethod=self.regrid_method, coordSys='deg',
                             diag={}, periodicity=1
                             )

            if self.target_mask is not None:
                if self.target_mask.shape != var.shape:
                    dummy, mask = genutil.grower(var, self.target_mask)
                else:
                    mask = self.target_mask
                var = MV2.masked_where(mask, var)

        return var

    def set_domain_in_var(self, var, region):
        domain = region.get('domain', None)
        if domain is not None:
            if isinstance(domain, dict):
                var = var(**domain)
            elif isinstance(domain, (list, tuple)):
                var = var(*domain)
            elif isinstance(domain, cdms2.selectors.Selector):
                domain.id = region.get("id", "region")
                var = var(*[domain])
        return var

    def set_file_mask_template(self):
        if isinstance(self.file_mask_template, basestring):
            self.file_mask_template = Base(self.root, self.file_mask_template,
                                           {'domain': self.region.get('domain', None)})

    def get_mask_from_var(self, var):
        try:
            o_mask = self.file_mask_template.get('sftlf')
        except:
            o_mask = cdutil.generateLandSeaMask(
                var, regridTool=self.regrid_tool).filled(1.) * 100.
            o_mask = MV2.array(o_mask)
            o_mask.setAxis(-1, var.getLongitude())
            o_mask.setAxis(-2, var.getLatitude())
        return o_mask

    def set_target_grid(self, target, regrid_tool='esmf',
                        regrid_method='linear'):
        self.regrid_tool = regrid_tool
        self.regrid_method = regrid_method
        if target == '2.5x2.5':
            self.target_grid = cdms2.createUniformGrid(
                -88.875, 72, 2.5, 0, 144, 2.5
            )
            self.target_grid_name = target
        elif cdms2.isGrid(target):
            self.target_grid = target
            self.target_grid_name = target
        else:
            logging.error('Unknown grid: %s' % target)
            raise RuntimeError('Unknown grid: %s' % target)

    def setup_cdms2(self):
        cdms2.setNetcdfShuffleFlag(0)  # Argument is either 0 or 1
        cdms2.setNetcdfDeflateFlag(0)  # Argument is either 0 or 1
        cdms2.setNetcdfDeflateLevelFlag(0)  # Argument is int between 0 and 9

    def hash(self, block_size=65536):
        self_file = open(self())
        buffer = self_file.read(block_size)
        hasher = hashlib.md5()
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = self_file.read(block_size)
        self_file.close()
        return hasher.hexdigest()


class JSONs(object):

    def addDict2Self(self, json_dict, json_struct, json_version, overwriteOnDuplicate=True):
        if float(json_version) == 1.0:
            V = json_dict[json_dict.keys()[0]]
            for model in V.keys():  # loop through models
                m = V[model]
                for ref in m.keys():
                    aref = m[ref]
                    if not(isinstance(aref, dict) and "source" in aref):  # not an obs key
                        continue
                    reals = aref.keys()
                    src = reals.pop(reals.index("source"))
                    for real in reals:
                        areal = aref[real]
                        areal2 = {"source": src}
                        for region in areal.keys():
                            reg = areal[region]
                            if region == "global":
                                region2 = ""
                            else:
                                region2 = region + "_"
                            areal2[region2 + "global"] = {}
                            areal2[region2 + "NHEX"] = {}
                            areal2[region2 + "SHEX"] = {}
                            areal2[region2 + "TROPICS"] = {}
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
                    reals = aref.keys()
                    src = reals.pop(reals.index("source"))
                    for real in reals:
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

    def __init__(self, files=[], structure=[], ignored_keys=[], oneVariablePerFile=True, overwriteOnDuplicate=True):
        self.json_version = 3.0
        self.json_struct = structure
        self.data = {}
        self.axes = None
        self.ignored_keys = ignored_keys
        self.oneVariablePerFile = oneVariablePerFile
        if len(files) == 0:
            raise Exception("You need to pass at least one file")

        for fnm in files:
            self.addJson(fnm,overwriteOnDuplicate=overwriteOnDuplicate)

    def addJson(self, filename, overwriteOnDuplicate=True):
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
        if json_struct != self.json_struct and self.json_struct == []:
            self.json_struct = json_struct
        self.addDict2Self(tmp_dict, json_struct, json_version, overwriteOnDuplicate=overwriteOnDuplicate)

    def getAxis(self, axis):
        axes = self.getAxisList()
        for a in axes:
            if a.id == axis:
                return a
        return None

    def getAxisIds(self):
        axes = self.getAxisList()
        return [ax.id for ax in axes]

    def getAxisList(self):
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
