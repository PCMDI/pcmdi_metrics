import pcmdi_metrics
import json
import os
import cdms2
import numpy
import MV2


class OBS(pcmdi_metrics.io.base.Base):

    def __init__(self, root, var, obs_dic, reference="default",
                 file_mask_template=None):

        template = "%(realm)/%(frequency)/%(variable)/" +\
            "%(reference)/%(ac)/%(filename)"
        pcmdi_metrics.io.base.Base.__init__(
            self, root, template, file_mask_template)
        obs_name = obs_dic[var][reference]
        # usually send "default", "alternate", etc
        # but some case (sftlf) we send the actual name
        if isinstance(obs_name, dict):
            obs_name = reference
        ref = obs_dic[var][obs_name]
        obs_table = ref["CMIP_CMOR_TABLE"]

        if obs_table == u"Omon":
            self.realm = 'ocn'
            self.frequency = 'mo'
            self.ac = 'ac'
        elif obs_table == u"fx":
            self.realm = ''
            self.frequency = 'fx'
            self.ac = ''
        else:
            self.realm = 'atm'
            self.frequency = 'mo'
            self.ac = 'ac'
        self.filename = ref["filename"]
        self.reference = obs_name
        self.variable = var

def flatten(dic,parent_key="",sep="__**__"):
    """ flattens a dictionary thanks stack overflow"""
    items = []
    for k, v in dic.items():
        if parent_key:
            new_key = "%s%s%s" % (parent_key,sep,k) 
        else:
            new_key = k
        if isinstance(v,dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key,v))
    return dict(items)

class JSONs(object):

    def getstruct(self):
        pass

    def sql(self,cmd):
        self.cu.execute(cmd)
        return self.cu.fetchall()

    def addJson(self,json_dict,json_struct,json_version):
        "Adds content of a json dict to the db"
        # first did we create the db
        # if yes what are the columns in it
        # do we need more columns??
        info = self.sql("PRAGMA table_info(pmp)")
        print "INFO DB PMP:",info

        if info == []:
            self.sql("PRAGMA FOREIGN_KEYS = ON")
            cols = "value FLOAT , "
            foreign = ""
            for c in json_struct:
                self.sql("create table %s (id INTEGER PRIMARY KEY AUTOINCREMENT, name char(25) UNIQUE ON CONFLICT IGNORE)" % c)
                cols+="%s INTEGER CHECK(TYPEOF(%s) = 'integer'), " % (c,c)
                foreign+="FOREIGN KEY(%s) REFERENCES %s(id) " % (c,c)
            self.sql("create table pmp (%s, %s)" % (cols[:-2], foreign))
            #self.sql("create table pmp (%s)" % (cols[:-2]))
        else:
            # ok let's check if we need more columns
            actual_cols = [str(i[1]) for i in info]
            add_cols = []
            for c in json_struct:
                if not str(c) in actual_cols:
                    add_cols.append(c)
            for c in add_cols:
                print "ADDING COLUMN:",c
                self.sql("create table %s (id INTEGER PRIMARY KEY AUTOINCREMENT, name char(25) UNIQUE ON CONFLICT REPLACE)" % c)
                self.sql("alter table pmp ADD COLUMN '%s' INTEGER CHECK(TYPEOF(%s))" % (c,c))
                self.sql("alter table pmp FOREIGN KEY(%s) REFERENCES %s(id)" % (c,c))

        # Ok at this point we have a db we now need to insert values in it
        f = flatten(json_dict)
        rows = []
        for ky in f.keys():
            values = ky.split("__**__")
            if float(json_version)==2.0:
                sp = values[-1].split("_")
                season = sp[-1]
                values[-1]="_".join(sp[:-1])
                values+=[season,]
            elif float(json_version)==1.0:
                sp = values[-1].split("_")
                if len(sp)<2:
                    continue
                reg = sp[-1]
                file_region = values[-2]
                if reg == "GBL":
                    reg = "global"
                if file_region == "global":
                    file_region = reg
                else:
                    file_region += "_"+reg
                values[-2]=file_region
                season = sp[-2]
                values[-1] = "_".join(sp[:-2])
                values.append("season")

            if len(values)!=len(json_struct):
                continue
            for k,v in zip(json_struct,values):
                if not (v,) in self.sql("select (name) from %s" % k):
                    self.sql("insert into %s (name) values ('%s')" % (k,v))
            for i,v in enumerate(values):
                val = self.sql("select id from %s where name='%s'" % (json_struct[i],v))
                values[i]=val[0][0]
            values.append(float(f[ky]))
            rows.append(values)
        keys = ", ".join(json_struct)+", value"
        qmarks = "?, " * (len(json_struct)+1)
        qry  = "INSERT into pmp (%s) VALUES (%s)"%(keys,qmarks[:-2])
        self.cu.executemany(qry,rows)
        self.db.commit()
        pass
    def __init__(self, files):
        import sqlite3
        import tempfile
        dbnm = tempfile.mktemp()
        dbnm = "Charles.sql"
        self.db = sqlite3.connect(dbnm)
        self.cu = self.db.cursor()
        self.data = {}
        self.json_version = "2.0"
        self.json_struct = ["model","reference","rip","region","statistic","season"]

        if len(files) == 0:
            raise Exception("You need to pass at least one file")
        for fnm in files:
            f = open(fnm)
            tmp_dict = json.load(f)
            json_version = tmp_dict.get("json_version", None)
            if json_version is None:
                # Json format not stored, trying to guess
                R = tmp_dict["RESULTS"]
                out = R[R.keys()[0]]  # get first available model
                out = out["defaultReference"]  # get first set of obs
                k = out.keys()
                k.pop(k.index("source"))
                out = out[k[0]]  # first realization
                # Ok at this point we need to see if it is json std 1 or 2
                # version 1 had NHEX in every region
                # version 2 does not
                if "bias_xy_djf_NHEX" in out[out.keys()[0]].keys():
                    json_version = "1.0"
                else:
                    json_version = "2.0"
            print "FILE:",fnm
            print "\tv%s" % json_version
            # Now update our stored results
            # First we need to figure out the variable read in
            json_struct = tmp_dict.get("json_structure",list(self.json_struct))
            print json_struct
            if not "variable" in json_struct:
                json_struct.insert(0,"variable")
                var = tmp_dict.get("Variable", None)
                if var is None:  # Not stored in json, need to get from file name
                    fnm = os.path.basename(fnm)
                    varnm = fnm.split("_")[0]
                else:
                    varnm = var["id"]
                    if "level" in var:
                        varnm += "-%i" % int(var["level"] / 100.)
                print "NEW DICT"
                tmp_dict = {varnm:tmp_dict["RESULTS"]}
            else:
                tmp_dict = tmp_dict["RESULTS"]
            self.addJson(tmp_dict,json_struct,json_version)

    def getAxis(self, axis):
        axes = self.getAxisList()
        for a in axes:
            if a.id == axis:
                return a
        return None

    def getAxisList(self):
        variables = self.data.keys()
        models = set()
        observations = set()
        rips = set()
        regions = set()
        stats = set()
        seasons = ['ann', 'mam', 'jja', 'son', 'djf']
        for v in variables:
            # print "Variable:",v
            V = self.data[v]
            models.update(V.keys())
            for m in V:
                # print "\tModel:",m
                M = V[m]
                for o in M:
                    O = M[o]
                    if isinstance(
                            O, dict) and "source" in O:  # ok it is indeed an obs key
                        # print "\t\tObs:",o
                        observations.update([o, ])
                        for r in O:
                            k = O.keys()
                            k.remove("source")
                            if r == "source":  # skip that one
                                continue
                            # print "\t\t\trip:",r
                            rips.update(k)
                            R = O[r]
                            Rkeys = R.keys()
                            if "source" in Rkeys:
                                Rkeys.remove("source")
                            for rg in Rkeys:
                                # print "\t\t\tregion:",rg
                                Rg = R[rg]
                                regions.update(Rkeys)
                                # print "REGIONS:",Rg
                                for s in Rg:
                                    stats.update([s[:-4], ])
                    else:
                        pass
        variable = cdms2.createAxis(sorted(variables), id="variable")
        model = cdms2.createAxis(sorted(models), id="model")
        observation = cdms2.createAxis(sorted(observations), id="observation")
        rip = cdms2.createAxis(sorted(rips), id="rip")
        region = cdms2.createAxis(sorted(regions), id="region")
        stat = cdms2.createAxis(sorted(stats), id="statistic")
        season = cdms2.createAxis(seasons, id="season")
        return [variable, model, observation, rip, region, stat, season]

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
        for i in range(sh[0]):
            # print
            # "VAR:",axes[0][i],"----------------------------------------------------------------______"
            try:
                val = self.data[axes[0][i]]  # select var
                for j in range(sh[1]):
                    # print "Model:",axes[1][j],type(val)
                    try:
                        val2 = val[axes[1][j]]  # select model
                        for k in range(sh[2]):
                            # print "OBS:",axes[2][k]
                            try:
                                val3 = val2[axes[2][k]]  # select obs
                                for l in range(sh[3]):
                                    # print "RIP:",axes[3][l]
                                    try:
                                        val4 = val3[axes[3][l]]  # select rip
                                        for m in range(sh[4]):
                                            # print "Reg:",axes[4][m]
                                            try:
                                                # select region
                                                val5 = val4[axes[4][m]]
                                                for n in range(sh[5]):
                                                    for o in range(sh[6]):
                                                        try:
                                                            val6 = val5[
                                                                axes[5][n] + "_" + axes[6][o]]
                                                        except:
                                                            val6 = 1.e20
                                                        # print val6
                                                        array[(i, j, k, l, m, n, o)] = float(
                                                            val6)
                                            except:  # Region not available?
                                                # print "NO REG"
                                                array[(i, j, k, l, m)] = 1.e20
                                    except:
                                        # print "NO RIP"
                                        array[(i, j, k, l)] = 1.e20
                            except:
                                # print "NO OBS"
                                array[(i, j, k)] = 1.e20
                    except Exception:
                        array[(i, j)] = 1.e20
            except:
                # print "NO VAR!"
                array[(i)] = 1.e20

        array = MV2.masked_greater(array, 9.e19)
        array.id = "pmp"
        array.setAxisList(axes)
        return array
