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

def recurs(out,ids,nms,axval,axes,cursor):
    if len(axes)>0:
        for i,val in enumerate(axes[0][:]):
             recurs(out,list(ids)+[i,],list(nms)+[axes[0].id],list(axval)+[val,],axes[1:],cursor)
    else:
        st = " and ".join(["%s='%s'"% (nm,val) for nm,val in zip(nms,axval)])
        qry = "select (value) from pmp where %s" % st
        cursor.execute(qry)
        val = cursor.fetchall()
        if len(val) == 0:
            print "QRY:",qry
            val = 1.e20
        elif len(val)==1:
            val =float(val[0][0])
        else:
            print "MULTIPLE ANSWERS",val
            val=1.e20

        out[tuple(ids)]=val

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
        self.cu.execute("PRAGMA main.page_size = 65536")
        self.cu.execute("PRAGMA main.cache_size = 65536")
        info = self.sql("PRAGMA table_info(pmp)")
        print "INFO DB PMP:",info

        if info == []:
            self.cu.execute("PRAGMA FOREIGN_KEYS = ON")
            cols = "value FLOAT , "
            for c in json_struct:
                cols+="%s CHAR(32), " % (c,)
            self.cu.execute("create table pmp (%s)" % (cols[:-2],))
        else:
            # ok let's check if we need more columns
            actual_cols = [str(i[1]) for i in info]
            add_cols = []
            for c in json_struct:
                if not str(c) in actual_cols:
                    add_cols.append(c)
            for c in add_cols:
                print "ADDING COLUMN:",c
                self.cu.execute("alter table pmp ADD COLUMN '%s' CHAR(32)" % (c,c))

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
                if reg == "GLB":
                    reg = "global"
                if file_region == "global":
                    file_region = reg
                else:
                    file_region += "_"+reg
                values[-2]=file_region
                season = sp[-2]
                values[-1] = "_".join(sp[:-2])
                values.append(season)

            if len(values)!=len(json_struct):
                continue
            #for k,v in zip(json_struct,values):
            #    #if not (v,) in self.sql("select (name) from %s" % k):
            #        self.cu.execute("insert into %s (name) values ('%s')" % (k,v))
            #for i,v in enumerate(values):
            #    val = self.sql("select id from %s where name='%s'" % (json_struct[i],v))
            #    values[i]=val[0][0]
            values.append(float(f[ky]))
            rows.append(values)
        keys = ", ".join(json_struct)+", value"
        qmarks = "?, " * (len(json_struct)+1)
        qry  = "INSERT into pmp (%s) VALUES (%s)"%(keys,qmarks[:-2])
        self.cu.executemany(qry,rows)
        #self.db.commit()
        pass
    def __init__(self, files=[], database = "Charles.sql"):
        import sqlite3
        import tempfile
        if database is None:
            dbnm = tempfile.mkfile()
        else:
            dbnm= database
        self.db = sqlite3.connect(dbnm)
        self.cu = self.db.cursor()
        self.data = {}
        self.json_version = "2.0"
        self.json_struct = ["model","reference","rip","region","statistic","season"]

        if len(files) == 0:
            if database is None:
                raise Exception("You need to pass at least one file or a database")
            elif self.sql("PRAGMA table_info(pmp)") == []:
                raise Exception("You need to pass at least one file or a non empty database")

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
        self.db.commit()

    def getAxis(self, axis):
        axes = self.getAxisList()
        for a in axes:
            if a.id == axis:
                return a
        return None

    def getAxisList(self):
        info = self.sql("PRAGMA table_info(pmp)")
        axes = []
        for ax in info[1:]:
            nm = str(ax[1])
            # now get all possible values for this
            #values = self.sql("select distinct %s from pmp" % nm)
            #print "VALUES:",values
            values = sorted([ str(a[0]) for a in self.sql("select distinct %s from pmp" % nm)])
            axes.append(cdms2.createAxis(values,id=nm))
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
        recurs(array,[],[],[],axes,self.cu)

        f = cdms2.open("charles.nc","w")
        f.write(array,id="pmp")
        f.close()
        array = MV2.masked_greater(array, 9.e19)
        array.id = "pmp"
        array.setAxisList(axes)
        return array
