import pcmdi_metrics
import json
import os
import cdms2

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
        for fnm in files:
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
                if "bias_xy_djf_NHEX" in out.keys():
                    json_version = "1.0"
                else:
                    json_version = "2.0"
            if json_version == "1.0":  # ok old way we need to convert to 2.0
                for model in R.keys():  # loop through models
                    m = R[model]
                    refs = m.keys()
                    refs.pop("SimulationDescription")
                    for ref in m.keys():
                        aref = m[ref]
                        reals = aref.keys()
                        src = reals.pop("source")
                        for real in reals:
                            areal = aref[real]
                            areal2={"source":src}
                            for region in areal.keys():
                                reg = areal[region]
                                if region == "global":
                                    region2 = ""
                                else:
                                    region2=region+"_"
                                areal2[region2+"global"]={}
                                areal2[region2+"NHEX"]={}
                                areal2[region2+"SHEX"]={}
                                areal2[region2+"TROPICS"]={}
                                key_stats = reg.keys()
                                for k in key_stats:
                                    if k[:7]=="custom_":
                                        areal2[region][k]=reg[k]
                                    else:
                                        sp = k.split("_")
                                        new_key = "_".join(sp[-1])
                                        domain = sp[-1]
                                        if domain == "GLB":
                                            domain = "global"
                                        areal2[region2+domain][new_key]=reg[k]
                            # Now we can replace the realization with the correctly formatted one
                            aref[areal] = areal2
                        # restore ref into model
                        m[ref]=aref
                    # restore model into results
                    R[m]=m
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
    def getAxisList(self):
        dimensions = ["variable","model","observation","rip","region","statistic","season"]
        variables = self.data.keys()
        models = set()
        observations=set()
        rips=set()
        regions=set()
        stats=set()
        seasons = set(['ann','djf','mam','jja','son'])
        for v in variables:
            print "Variable:",v
            V = self.data[v]
            models.update(V.keys())
            for m in V:
                print "\tModel:",m
                M=V[m]
                for o in M:
                    O=M[o]
                    if isinstance(O,dict) and O.has_key("source"):  # ok it is indeed an obs key
                        print "\t\tObs:",o
                        observations.update([o,])
                        for r in O:
                            if r == "source":  #skip that one
                                continue
                            print "\t\t\trip:",r
                            R=O[r]
                            rips.update(R.keys())
                            for rg in R:
                                print "\t\t\tregion:",rg
                                Rg = R[rg]
                                regions.update(Rg.keys())
                                for s in Rg:
                                    stats.update([s[:-4],])
                    else:
                        pass
        variables = cdms2.createAxis(sorted(variables),id="variables")
        models = cdms2.createAxis(sorted(models),id="models")
        print models

