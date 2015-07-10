import pcmdi_metrics


class OBS(pcmdi_metrics.io.base.Base):

    def __init__(self, root, var, obs_dic, reference="default"):

        template = "%(realm)/%(frequency)/%(variable)/" +\
            "%(reference)/%(ac)/%(filename)"
        pcmdi_metrics.io.base.Base.__init__(self, root, template)
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
