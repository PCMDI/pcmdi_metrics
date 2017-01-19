import logging
import MV2
import pcmdi_metrics.io.pmp_io
import pcmdi_metrics.driver.dataset


class OBS(pcmdi_metrics.io.pmp_io.PMPIO):
    def __init__(self, root, var, obs_dict, obs='default',
                 file_mask_template=None):
        template = "%(realm)/%(frequency)/%(variable)/" +\
                   "%(reference)/%(ac)/%(filename)"
        super(OBS, self).__init__(root, template, file_mask_template)

        logging.basicConfig(level=logging.DEBUG)

        if obs not in obs_dict[var]:
            msg = '%s is not a valid obs according to the obs_dict.' % obs
            raise RuntimeError(msg)
        obs_name = obs_dict[var][obs]
        # Sometimes (when sftlf), we send the actually name of the obs
        if isinstance(obs_name, dict):
            obs_name = obs

        obs_table = obs_dict[var][obs_name]['CMIP_CMOR_TABLE']
        self.realm = ''
        self.frequency = ''
        self.ac = ''
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


class Observation(pcmdi_metrics.driver.dataset.DataSet):
    def __init__(self, parameter, var_name_long, region,
                 obs, obs_dict, data_path, sftlf):
        super(Observation, self).__init__(parameter, var_name_long, region,
                                          obs_dict, data_path, sftlf)
        self._obs_file = None
        self.obs_or_model = obs
        self.create_obs_file()
        self.setup_target_grid(self._obs_file)
        self.setup_target_mask()

    def create_obs_file(self):
        obs_mask_name = self.create_obs_mask_name()
        self._obs_file = OBS(self.data_path, self.var,
                             self.obs_dict, self.obs_or_model,
                             file_mask_template=obs_mask_name)
        self.apply_custom_keys(self._obs_file,
                               self.parameter.custom_keys, self.var)
        self._obs_file.case_id = self.parameter.case_id

    def create_obs_mask_name(self):
        try:
            obs_from_obs_dict = self.get_obs_from_obs_dict()
            obs_mask = OBS(self.data_path, 'sftlf',
                           self.obs_dict, obs_from_obs_dict['RefName'])
            obs_mask_name = obs_mask()
        except:
            msg = 'Could not figure out obs mask name from obs json file'
            logging.info(msg)
            obs_mask_name = None

        return obs_mask_name

    def get_obs_from_obs_dict(self):
        if isinstance(self.obs_dict[self.var][self.obs_or_model], (str, unicode)):
            obs_from_obs_dict = \
                self.obs_dict[self.var][self.obs_dict[self.var][self.obs_or_model]]
        else:
            obs_from_obs_dict = self.obs_dict[self.var][self.obs_or_model]
        return obs_from_obs_dict

    def setup_target_mask(self):
        if self.region is not None:
            region_value = self.region.get('value', None)
            if region_value is not None:
                self._obs_file.target_mask = MV2.not_equal(
                    self.sftlf['target_grid'],
                    region_value
                )

    def get(self):
        try:
            if self.level is not None:
                data_obs = self._obs_file.get(self.var,
                                              level=self.level,
                                              region=self.region)
            else:
                data_obs = self._obs_file.get(self.var,
                                              region=self.region)
            return data_obs
        except Exception as e:
            if self.level is not None:
                logging.error('Failed opening 4D OBS',
                              self.var, self.obs_or_model, e)
            else:
                logging.error('Failed opening 3D OBS',
                              self.var, self.obs_or_model, e)

    def hash(self):
        return self._obs_file.hash()

    def file_path(self):
        return self._obs_file()

    @staticmethod
    # This must remain static b/c used before an Observation obj is created.
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
