import pcmdi_metrics
import json
import os
import cdms2
import numpy
import MV2

class OBS(pcmdi_metrics.io.base.Base):

    def __init__(self, root, var, obs_dic, reference="default", file_mask_template=None):

        template = "%(realm)/%(frequency)/%(variable)/" +\
            "%(reference)/%(ac)/%(filename)"
        pcmdi_metrics.io.base.Base.__init__(self, root, template, file_mask_template)
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

class JSONs(object):
    def __init__(self,files):
        self.data = {}
        self.json_version = "2.0"
        if len(files)==0:
            raise Exception("You need to pass at least one file")
        for fnm in files:
            #print fnm
            f=open(fnm)
            tmp_dict=json.load(f)
            json_version=tmp_dict.get("json_version",None)
            if json_version is None:
                # Json format not stored, trying to guess
                R = tmp_dict["RESULTS"]
                out = R[R.keys()[0]]  # get first available model
                out=out["defaultReference"]  # get first set of obs
                k = out.keys()
                k.pop(k.index("source"))
                out = out[k[0]] # first realization
                # Ok at this point we need to see if it is json std 1 or 2
                # version 1 had NHEX in every region
                # version 2 does not
                if "bias_xy_djf_NHEX" in out[out.keys()[0]].keys():
                    json_version = "1.0"
                else:
                    json_version = "2.0"
            # print "\tv%s" % json_version
            if json_version == "1.0":  # ok old way we need to convert to 2.0
                for model in R.keys():  # loop through models
                    #print "Reading in model:",model
                    m = R[model]
                    #print "FIRST M:",m.keys()
                    refs = m.keys()
                    for ref in m.keys():
                        aref = m[ref]
                        if not(isinstance(aref,dict) and aref.has_key("source")):  #not an obs key
                            continue
                        #print "\treading in ref:",ref
                        # print aref.keys()
                        reals = aref.keys()
                        src = reals.pop(reals.index("source"))
                        for real in reals:
                            #print "\t\treading in realization:",real
                            # print real
                            areal = aref[real]
                            areal2={"source":src}
                            for region in areal.keys():
                                #print "\t\t\tREGION:",region
                                reg = areal[region]
                                if region == "global":
                                    region2 = ""
                                else:
                                    region2=region+"_"
                                areal2[region2+"global"]={}
                                areal2[region2+"NHEX"]={}
                                areal2[region2+"SHEX"]={}
                                areal2[region2+"TROPICS"]={}
                                # print "OK HERE REGIONS:",areal2.keys()
                                key_stats = reg.keys()
                                for k in key_stats:
                                    if k[:7]=="custom_":
                                        areal2[region][k]=reg[k]
                                    else:
                                        #print "SPLITTING:",k
                                        sp = k.split("_")
                                        new_key = "_".join(sp[:-1])
                                        domain = sp[-1]
                                        if domain == "GLB":
                                            domain = "global"
                                        if new_key.find("rms_xyt")>-1: print "\t\t\t\tregion, stats:",region2+domain,new_key,reg[k]
                                        areal2[region2+domain][new_key]=reg[k]
                            # Now we can replace the realization with the correctly formatted one
                            #print "AREAL@:",areal2
                            aref[real] = areal2
                        # restore ref into model
                        m[ref]=aref
                    # restore model into results
                    R[model]=m
                    #print "M:",model,m.keys()
            # Now update our stored results
            # First we need to figure out the variable read in
            var = tmp_dict.get("Variable",None)
            if var is None:  # Not stored in json, need to get from file name
                fnm = os.path.basename(fnm)
                varnm = fnm.split("_")[0]
            else:
                varnm = var["id"]
                if hasattr(var,"level"):
                    varnm+="-"+int(var["level"]/100.)
            if self.data.has_key(varnm):
                self.data[varnm].update(R)
            else:
                self.data[varnm]=R
    def getAxis(self,axis):
        axes = self.getAxisList()
        for a in axes:
            if a.id == axis:
                return a
        return None

    def getAxisList(self):
        dimensions = ["variable","model","observation","rip","region","statistic","season"]
        variables = self.data.keys()
        models = set()
        observations=set()
        rips=set()
        regions=set()
        stats=set()
        seasons = ['ann','mam','jja','son','djf']
        for v in variables:
            #print "Variable:",v
            V = self.data[v]
            models.update(V.keys())
            for m in V:
                #print "\tModel:",m
                M=V[m]
                for o in M:
                    O=M[o]
                    if isinstance(O,dict) and O.has_key("source"):  # ok it is indeed an obs key
                        #print "\t\tObs:",o
                        observations.update([o,])
                        for r in O:
                            k = O.keys()
                            k.remove("source")
                            if r == "source":  #skip that one
                                continue
                            #print "\t\t\trip:",r
                            rips.update(k)
                            R=O[r]
                            Rkeys = R.keys()
                            if "source" in Rkeys: Rkeys.remove("source")
                            for rg in Rkeys:
                                #print "\t\t\tregion:",rg
                                Rg = R[rg]
                                regions.update(Rkeys)
                                #print "REGIONS:",Rg
                                for s in Rg:
                                    stats.update([s[:-4],])
                    else:
                        pass
        variable = cdms2.createAxis(sorted(variables),id="variable")
        model = cdms2.createAxis(sorted(models),id="model")
        observation = cdms2.createAxis(sorted(observations),id="observation")
        rip = cdms2.createAxis(sorted(rips),id="rip")
        region = cdms2.createAxis(sorted(regions),id="region")
        stat = cdms2.createAxis(sorted(stats),id="statistic")
        season = cdms2.createAxis(seasons,id="season")
        return [variable,model,observation,rip,region,stat,season]

    def __call__(self,**kargs):
        """ Returns the array of values"""
        axes = self.getAxisList()
        sh=[]
        ids = []
        for a in axes:
            sh.append(len(a)) # store length to construct array shape
            ids.append(a.id)  # store ids

        # first let's see which vars are actually asked for
        # for now assume all keys means restriction on dims
        for axis_id in kargs:
            if not axis_id in ids:
                raise ValueError("Invalid axis '%s'" % axis_id)
            index = ids.index(axis_id)
            value = kargs[axis_id]
            if isinstance(value,basestring):
                value = [value]
            if not isinstance(value,(list,tuple,slice)):
                raise TypeError("Invalid subsetting type for axis '%s', axes can only be subsetted by string,list or slice"%s)
            if isinstance(value,slice):
                axes[index]=axes[index].subAxis(value.start,value.stop,value.step)
                sh[index]=len(axes[index])
            else:  # ok it's a list
                for v in value:
                    if not v in axes[index][:]:
                        raise ValueError("Unkwown value '%s' for axis '%s'" % (v,axis_id))
                axis = cdms2.createAxis(value,id=axes[index].id)
                axes[index] = axis
                sh[index] = len(axis)

        array = numpy.ma.ones(sh,dtype=numpy.float)

        # Now let's fill this array
        for i in range(sh[0]):
            #print "VAR:",axes[0][i]
            try:
                val = self.data[axes[0][i]]  # select var
                for j in range(sh[1]):
                    #print "Model:",axes[1][j],type(val)
                    try:
                        val2=val[axes[1][j]] # select model
                        for k in range(sh[2]):
                            #print "OBS:",axes[2][k]
                            try:
                                val3=val2[axes[2][k]]  # select obs
                                for l in range(sh[3]):
                                    #print "RIP:",axes[3][l]
                                    try:
                                        val4=val3[axes[3][l]]  # select rip
                                        for m in range(sh[4]):
                                            #print "Reg:",axes[4][m]
                                            try:
                                                val5=val4[axes[4][m]]  # select region
                                                for n in range(sh[5]):
                                                    for o in range(sh[6]):
                                                        try:
                                                            val6 = val5[axes[5][n]+"_"+axes[6][o]]
                                                        except:
                                                            val6 = 1.e20
                                                        array[(i,j,k,l,m,n,o)] = float(val6)
                                            except: # Region not available?
                                                #print "NO REG"
                                                array[(i,j,k,l,m)]=1.e20
                                    except:
                                        #print "NO RIP"
                                        array[(i,j,k,l)]=1.e20
                            except:
                                #print "NO OBS"
                                array[(i,j,k)]=1.e20
                    except Exception,err:
                        #print "NO MODEL",err
                        array[(i,j)]=1.e20
            except:
                #print "NO VAR!"
                array[(i)]=1.e20

        array = MV2.array(array,id="pmp")
        array.setAxisList(axes)
        return array


