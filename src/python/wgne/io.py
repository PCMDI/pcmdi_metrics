import metrics
class OBS(metrics.io.base.Base):
    def __init__(self,root,var,obs_dic,reference="default"):
      
        template = "%(realm)/mo/%(variable)/%(reference)/ac/%(variable)_pcmdi-metrics_%(obs_table)_%(reference)_%(period)-clim.%(ext)" 
        metrics.io.base.Base.__init__(self,root,template)
        obs_name = obs_dic[var][reference]
        ref = obs_dic[var][obs_name]
        period = ref["period"]
        self.obs_table = ref["CMIP_CMOR_TABLE"]
 
#       template = "%s/%s/ac/%s_%s_%%(period)_ac.%%(ext)" % (var,obs_dic[var][reference],var,obs_dic[var][reference])


#       template = "%s/%s/ac/%s_pcmdi-metrics%%(obs_realm)_%s_%%(period)-clim.%%(ext)" % (var,obs_dic[var][reference],var,obs_dic[var][reference])


        if self.obs_table == u"Omon":
            self.realm = 'ocn'
        else:
            self.realm = 'atm'
        self.period = period
        self.ext = "nc"
        self.reference=obs_name
        self.variable=var


