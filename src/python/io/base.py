import json
import cdms2
import MV2
import cdutil
import genutil
import os
import pcmdi_metrics
import cdat_info
import hashlib
import numpy

value = 0
cdms2.setNetcdfShuffleFlag(value)  # where value is either 0 or 1
cdms2.setNetcdfDeflateFlag(value)  # where value is either 0 or 1
# where value is a integer between 0 and 9 included
cdms2.setNetcdfDeflateLevelFlag(value)

# cdutil region object need a serializer


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
            data["metrics_git_sha1"] = pcmdi_metrics.__git_sha1__
            data["uvcdat_version"] = cdat_info.get_version()
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


def recurs(out, ids, nms, axval, axes, cursor, table_name):
    if len(axes) > 0:
        for i, val in enumerate(axes[0][:]):
            recurs(out, list(ids) +
                   [i, ], list(nms) +
                   [axes[0].id], list(axval) +
                   [val, ], axes[1:], cursor, table_name)
    else:
        st = " and ".join(["%s='%s'" % (nm, val) for nm, val in zip(nms, axval)])
        qry = "select (value) from %s where %s" % (table_name, st)
        cursor.execute(qry)
        val = cursor.fetchall()
        if len(val) == 0:
            # print "QRY:",qry
            val = 1.e20
        elif len(val) == 1:
            val = float(val[0][0])
        else:
            print "MULTIPLE ANSWERS FOR:", zip(nms, axval)
            val = 1.e20

        out[tuple(ids)] = val


def flatten(dic, parent_key="", sep="__**__"):
    """ flattens a dictionary thanks stack overflow"""
    items = []
    for k, v in dic.items():
        if parent_key:
            new_key = "%s%s%s" % (parent_key, sep, k)
        else:
            new_key = k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class JSONs(object):

    def getstruct(self):
        pass

    def sql(self, cmd):
        self.cu.execute(cmd)
        return self.cu.fetchall()

    def addDict2DB(self, json_dict, json_struct, json_version):
        "Adds content of a json dict to the db"
        # first did we create the db
        # if yes what are the columns in it
        # do we need more columns??
        self.cu.execute("PRAGMA main.page_size = 65536")
        self.cu.execute("PRAGMA main.cache_size = 65536")
        info = self.sql("PRAGMA table_info(%s)" % self.table_name)

        if info == []:
            self.cu.execute("PRAGMA FOREIGN_KEYS = ON")
            cols = "value FLOAT , "
            for c in json_struct:
                cols += "%s CHAR(32), " % (c,)
            self.cu.execute("create table %s (%s)" % (self.table_name, cols[:-2],))
        else:
            # Let's figure out our db struct
            db_struct = [str(a[1]) for a in info[1:]]
            if json_struct != db_struct:
                raise RuntimeError(
                    "JSON file struct: %s is not compatible with db struct %s" %
                    (json_struct, db_struct))

        # Ok at this point we have a db we now need to insert values in it
        f = flatten(json_dict)
        rows = []
        for ky in f.keys():
            values = ky.split("__**__")
            if float(json_version) == 2.0:
                sp = values[-1].split("_")
                season = sp[-1]
                values[-1] = "_".join(sp[:-1])
                values += [season, ]
            elif float(json_version) == 1.0:
                sp = values[-1].split("_")
                if len(sp) < 2:
                    continue
                reg = sp[-1]
                file_region = values[-2]
                if reg == "GLB":
                    reg = "global"
                if file_region == "global":
                    file_region = reg
                else:
                    file_region += "_" + reg
                values[-2] = file_region
                season = sp[-2]
                values[-1] = "_".join(sp[:-2])
                values.append(season)

            if len(values) != len(json_struct):
                continue
            values.append(float(f[ky]))
            rows.append(values)
        keys = ", ".join(json_struct) + ", value"
        qmarks = "?, " * (len(json_struct) + 1)
        qry = "INSERT into %s (%s) VALUES (%s)" % (self.table_name, keys, qmarks[:-2])
        self.cu.executemany(qry, rows)
        # self.db.commit()
        pass

    def __init__(self, files=[], database=None, structure=[], table_name="pmp"):
        import sqlite3
        import tempfile
        if database is None:
            dbnm = tempfile.mktemp()
        else:
            dbnm = database
        self.table_name = table_name
        self.db = sqlite3.connect(dbnm)
        self.cu = self.db.cursor()
        self.json_version = 3.0
        self.json_struct = structure
        if len(files) == 0:
            if database is None:
                raise Exception("You need to pass at least one file or a database")
            elif self.sql("PRAGMA table_info(%s)" % self.table_name) == []:
                raise Exception("You need to pass at least one file or a non empty database")

        for fnm in files:
            self.addJson(fnm)

    def addJson(self, filename):
        f = open(filename)
        tmp_dict = json.load(f)
        json_struct = tmp_dict.get("json_structure", list(self.json_struct))
        json_version = tmp_dict.get("json_version", None)
        if "variable" not in json_struct:
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
        self.addDict2DB(tmp_dict, json_struct, json_version)

    def getAxis(self, axis):
        axes = self.getAxisList()
        for a in axes:
            if a.id == axis:
                return a
        return None

    def getAxisList(self):
        info = self.sql("PRAGMA table_info(%s)" % self.table_name)
        axes = []
        for ax in info[1:]:
            nm = str(ax[1])
            # now get all possible values for this
            values = sorted([str(a[0]) for a in self.sql("select distinct %s from %s" % (nm, self.table_name))])
            axes.append(cdms2.createAxis(values, id=nm))
        return axes

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
        recurs(array, [], [], [], axes, self.cu, self.table_name)

        array = MV2.masked_greater(array, 9.e19)
        array.id = self.table_name
        array.setAxisList(axes)
        return array
