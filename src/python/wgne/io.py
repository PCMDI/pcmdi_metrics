import metrics
class OBS(metrics.io.base.Base):
    def __init__(self,root,var,obs_dic,reference="default"):
      
        obs_name = obs_dic[var][reference]
        ref = obs_dic[var][obs_name]
        period = ref["period"]
        self.obs_realm = ref["CMIP_CMOR_TABLE"]
 
#       template = "%s/%s/ac/%s_%s_%%(period)_ac.%%(ext)" % (var,obs_dic[var][reference],var,obs_dic[var][reference])
        template = "%s/%s/ac/%s_pcmdi-metrics_%%(obs_realm)_%s(obs_name)_%%(period)-clim.%%(ext)" % (var,obs_dic[var][reference],var,obs_dic[var][reference])

        if var in ['tos','sos','zos']: 
          template = "%s/%s/ac/%s_pcmdi-metrics_Omon_%s_%%(period)-clim.%%(ext)" % (var,obs_dic[var][reference],var,obs_dic[var][reference]) 
        if var not in ['tos','sos','zos']:
          template = "%s/%s/ac/%s_pcmdi-metrics_Amon_%s_%%(period)-clim.%%(ext)" % (var,obs_dic[var][reference],var,obs_dic[var][reference])

#       template = "%s/%s/ac/%s_pcmdi-metrics%%(obs_realm)_%s_%%(period)-clim.%%(ext)" % (var,obs_dic[var][reference],var,obs_dic[var][reference])


        metrics.io.base.Base.__init__(self,root,template)
        #if self.obs_realm == u"Omon"
        #    self.realm = 'ocn'
        #else:
        #    self.realm = 'atm'
        self.period = period
        self.ext = "nc"

