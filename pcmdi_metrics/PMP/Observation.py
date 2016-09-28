from pcmdi_metrics.PMP.PMPIO import *



class OBS(PMPIO):
    def __init__(self, root, var, obs_dict, obs='default',
                 file_mask_template=None):
        template = "%(realm)/%(frequency)/%(variable)/" +\
                   "%(reference)/%(ac)/%(filename)"
        super(OBS, self).__init__(root, template, file_mask_template)

        if obs not in obs_dict[var]:
            msg = '%s is not a valid obs according to the obs_dict.' % obs
            raise RuntimeError(msg)
        obs_name = obs_dict[var][obs]
        # Sometimes (when sftlf), we send the actually name of the obs
        if isinstance(obs_name, dict):
            obs_name = obs

        obs_table = obs_dict[var][obs_name]['CMIP_CMOR_TABLE']
        self.setup_based_on_obs_table(obs_table)

        self.filename = obs_dict[var][obs_name]['filename']
        self.reference = obs_name
        self.variable = var

    def setup_based_on_obs_table(self, obs_table):
        if obs_table == u'Omon':
            self.realm = 'ocn'
            self.frequency = 'mo'
            self.ac = 'ac'
        elif obs_table == u'fx':
            self.realm = ''
            self.frequency = 'fx'
            self.ac = ''
        else:
            self.realm = 'atm'
            self.frequency = 'mo'
            self.ac = 'ac'


class Observation(object):
    def __init__(self, parameter, var, obs, obs_dict):
        self.parameter = parameter
        self.var = var
        self.obs = obs
        self.obs_dict = obs_dict

        string_template = "%(var)%(level)_%(targetGridName)_" +\
                          "%(regridTool)_%(regridMethod)_metrics"
        self.obs_file = PMPIO(self.parameter.metrics_output_path,
                              string_template)

    @staticmethod
    # This must remain static.
    def setup_obs_list_from_parameter(parameter_obs_list, obs_dict, var):
        obs_list = parameter_obs_list
        if 'all' in [x.lower() for x in obs_list]:
            obs_list = 'all'
        if isinstance(obs_list, (unicode, str)):
            if obs_list.lower() == 'all':
                obs_list = []
                for obs in obs_dict[var].keys():
                    if isinstance(obs_dict[var][obs], (unicode, str)):
                        obs_list.append(obs)
            else:
                obs_list = [obs_list]
        return obs_list

    def something(self):
        obs_mask_name = self.create_obs_mask_name()

    def create_obs_mask_name(self):
        try:
            if isinstance(self.obs_dict[self.var][self.obs], (str, unicode)):
                obs_from_obs_dict = self.obs_dict[self.var][self.obs_dict[self.var][self.obs]]
            else:
                obs_from_obs_dict = self.obs_dict[self.var][self.obs]
            obs_mask = OBS(self.parameter.obs_data_path, 'sftlf',
                           self.obs_dict, obs_from_obs_dict['RefName'])
            obs_mask_name = obs_mask()
        except:
            msg = 'Could not figure out obs mask name from obs json file'
            logging.error(msg)
            obs_mask_name = None
        return obs_mask_name

