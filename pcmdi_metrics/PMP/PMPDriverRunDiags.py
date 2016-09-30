import logging
import os
import sys
import json
import collections
from pcmdi_metrics.PMP.PMPParameter import *
import pcmdi_metrics.PMP.OutputMetrics


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
                self.setup_obs_or_model_or_output_file(self.output_metric)

                self.regions_loop()


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

        def regions_loop(self):
            self.regions_dict = self.create_regions_dict()

            for self.region in self.region_dict[self.var]:
                # Runs obs vs obs, obs vs model, or model vs model
                self.run_data_a_and_data_b_comparison(self.obs_dict)

        def create_regions_dict(self):
            default_regions = []

            # This loads the regions_specs and default_regions var into
            # the namespace of this scope.
            default_regions_file = \
                self.load_path_as_file_obj('default_regions.py')
            execfile(default_regions_file.name)

            regions_dict = {}
            for var_name_long in self.parameter.vars:
                var = var_name_long.split('_')[0]
                regions = self.parameter.regions
                region = regions.get(var, default_regions)
                if not isinstance(region, (list, tuple)):
                    region = [region]
                if region is None:
                    region.remove(None)
                    for r in default_regions:
                        region.insert(0, r)
                regions_dict[var] = region

            return regions_dict

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
            # element_a/b is either an obs or model
            for self.element_a in self.parameter.data_set_a:
                cls = \
                    self.determine_obs_or_model_class_instance(self.data_set_a_is_obs)
                self.data_set_a = cls(self.parameter, self.var, self.element_a)


        @staticmethod
        def determine_obs_or_model_class_instance(is_obs):
            if is_obs:
                # return Observation
                pass
            else:
                #return Model
                pass

        @staticmethod
        def calculate_level_from_var(var):
            var_split_name = var.split('_')
            if len(var_split_name) > 1:
                level = float(var_split_name[-1]) * 100
            else:
                level = None
            return level
