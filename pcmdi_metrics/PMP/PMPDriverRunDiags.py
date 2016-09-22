import logging
import os
import sys
import json
import collections
from pcmdi_metrics.PMP.PMPParameter import *
import pcmdi_metrics.PMP.OutputMetrics

def THINGTHINGTHING():
    return 'nothign'

class PMPDriverRunDiags(object):

        def __init__(self, parameter):
            self.parameter = parameter
            self.regrid_method = ''
            self.regrid_tool = ''
            self.table_realm = ''
            self.realm = ''

        def __call__(self, *args, **kwargs):
            self.run_diags()

        def run_diags(self):
            for self.var_name_long in self.parameter.vars:
                self.var = self.var_name_long.split('_')[0]
                self.obs_dict = self.load_obs_dict()

                if self.use_omon(self.obs_dict, self.var):
                    self.regrid_method = self.parameter.regrid_method_ocn
                    self.regrid_tool = self.regrid_tool_ocn.regrid_tool
                    self.table_realm = 'Omon'
                    self.realm = 'ocn'
                else:
                    self.regrid_method = self.parameter.regrid_method
                    self.regrid_tool = self.parameter.regrid_tool
                    self.table_realm = 'Amon'
                    self.realm = 'atm'

                self.output_metric =\
                    pcmdi_metrics.PMP.OutputMetrics.OutputMetrics\
                        (self.parameter, self.var_name_long)

                # Runs obs vs obs, obs vs model, or model vs model
                self.run_data_a_and_data_b_comparison(self.obs_dict)


        def load_obs_dict(self):
            obs_file_name = 'obs_info_dictionary.json'
            obs_json_file = self.load_path_as_file_obj(obs_file_name)
            obs_dic = json.loads(obs_json_file.read())
            obs_json_file.close()
            return obs_dic

        @staticmethod
        def load_path_as_file_obj(name):
            file_path = os.path.join(os.path.dirname(__file__), 'share', name)
            try:
                opened_file = open(file_path)
            except IOError:
                logging.error('%s could not be loaded!' % file_path)
                print 'IOError: %s could not be loaded!' % file_path
            except:
                logging.error('Unexpected error while opening file: '
                              + sys.exc_info()[0])
                print ('Unexpected error while opening file: '
                       + sys.exc_info()[0])
            return opened_file

        @staticmethod
        def use_omon(obs_dict, var):
            return \
                obs_dict[var][obs_dict[var]["default"]]["CMIP_CMOR_TABLE"] ==\
                'Omon'

        @staticmethod
        def calculate_level_from_var(var):
            var_split_name = var.split('_')
            if len(var_split_name) > 1:
                level = float(var_split_name[-1]) * 100
            else:
                level = None
            return level

        def setup_obs_or_model_or_output_file(self, io_file):
            io_file.set_target_grid(self.regrid_tool, self.regrid_method)
            io_file.set_var(self.var)
            io_file.set_realm(self.realm)
            io_file.set_table(self.table_realm)

        def run_data_a_and_data_b_comparison(self):
            data_set_a = self.parameter.data_set_a
            data_set_b = self.parameter.data_set_b

            # Member variables are used so when it's obs_vs_model, we know
            # which is which.
            self.data_set_a_is_obs = self.is_data_set_obs(data_set_a)
            self.data_set_b_is_obs = self.is_data_set_obs(data_set_b)

            if self.data_set_a_is_obs and self.data_set_b_is_obs:
                logging.info('Running obs vs obs.')
                self.obs_vs_obs()

            if not self.data_set_a_is_obs and not self.data_set_b_is_obs:
                logging.info('Running model vs model.')
                self.model_vs_model()

            if (not self.data_set_a_is_obs and self.data_set_b_is_obs) or \
               (self.data_set_a_is_obs and not self.data_set_b_is_obs):
                logging.info('Running obs vs obs.')
                self.obs_vs_model()

        def is_data_set_obs(self, data_set, obs_dict):
            data_set_is_obs = True

            # If an element of data_a is not in the obs_dict, then data_a is
            # a model.
            for obs in data_set:
                if obs not in obs_dict[self.var]:
                    data_set_is_obs = False

            return data_set_is_obs

        def obs_vs_model(self):
            pass
