from pcmdi_metrics.PMP.PMPIO import *
from pcmdi_metrics.PMP.DataSet import *


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


class Observation(DataSet):
    def __init__(self, parameter, var_name_long, region,
                 obs, obs_dict, sftlf=None):
        super(Observation, self).__init__(parameter, var_name_long,
                                          region, obs_dict, sftlf)
        self.obs_or_model = obs
        # This is just to make it more clear.
        self.obs_file = self.obs_or_model_file

        self.create_obs_file()

    def create_obs_file(self):
        obs_mask_name = self.create_obs_mask_name()
        self.obs_file = OBS(self.parameter.obs_data_path, self.var,
                            self.obs_dict, self.obs_or_model,
                            file_mask_template=obs_mask_name)

        self.setup_obs_file()

    def create_obs_mask_name(self):
        try:
            obs_from_obs_dict = self.get_obs_from_obs_dict()
            obs_mask = OBS(self.parameter.obs_data_path, 'sftlf',
                           self.obs_dict, obs_from_obs_dict['RefName'])
            obs_mask_name = obs_mask()
        except:
            msg = 'Could not figure out obs mask name from obs json file'
            logging.error(msg)
            obs_mask_name = None
        return obs_mask_name

    def get_obs_from_obs_dict(self):
        if self.obs_or_model not in self.obs_dict[self.var]:
            raise KeyError('The selected obs is not in the obs_dict')

        if isinstance(self.obs_dict[self.var][self.obs_or_model], (str, unicode)):
            obs_from_obs_dict = \
                self.obs_dict[self.var][self.obs_dict[self.var][self.obs_or_model]]
        else:
            obs_from_obs_dict = self.obs_dict[self.var][self.obs_or_model]
        return obs_from_obs_dict

    def setup_obs_file(self):
        if self.use_omon(self.obs_dict, self.var):
            regrid_method = self.parameter.regrid_method_ocn
            regrid_tool = self.parameter.regrid_tool
            self.obs_file.table = 'Omon'
            self.obs_file.realm = 'ocn'
        else:
            regrid_method = self.parameter.regrid_method
            regrid_tool = self.parameter.regrid_tool
            self.obs_file.table = 'Amon'
            self.obs_file.realm = 'atm'

        self.obs_file.set_target_grid(self.parameter.target_grid,
                                      regrid_tool,
                                      regrid_method)
        if self.region is not None:
            region_value = self.region.get('value', None)
            if region_value is not None:
                if self.sftlf is None:
                    self.sftlf = self.create_sftlf(self.parameter)
                self.obs_file.targetMask = MV2.not_equal(
                    self.sftlf['target_grid'],
                    region_value
                )

    def get(self):
        if self.level is not None:
            return self.obs_file.get_var_from_netcdf(self.var,
                                                     level=self.level,
                                                     region=self.region)
        else:
            return self.obs_file.get_var_from_netcdf(self.var,
                                                     region=self.region)

    def hash(self):
        return self.obs_file.hash()

    def file_path(self):
        return self.obs_file()

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
