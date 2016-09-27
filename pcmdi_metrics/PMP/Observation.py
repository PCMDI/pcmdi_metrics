from pcmdi_metrics.PMP.PMPIO import *


class Observation(object):
    def __init__(self, parameter, var, obs):
        self.parameter = parameter
        self.var = var
        self.obs = obs

        string_template = "%(var)%(level)_%(targetGridName)_" +\
                  "%(regridTool)_%(regridMethod)_metrics"
        self.obs_file = PMPIO(self.parameter.metrics_output_path,
                              string_template)

    @staticmethod
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
