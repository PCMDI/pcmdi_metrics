import logging
import os
import sys
import json
import collections
from pcmdi_metrics.PMP.PMPParameter import *
import pcmdi_metrics.PMP.OutputMetrics
from pcmdi_metrics.PMP.Observation import *
from pcmdi_metrics.PMP.Model import *

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
            self.obs_dict = self.load_obs_dict()
            self.regions_dict = self.create_regions_dict()

            for self.var_name_long in self.parameter.vars:
                self.var = self.var_name_long.split('_')[0]

                self.output_metric =\
                    pcmdi_metrics.PMP.OutputMetrics.OutputMetrics\
                        (self.parameter, self.var_name_long, self.obs_dict)

                for self.region in self.region_dict[self.var]:


                    # Runs obs vs obs, obs vs model, or model vs model
                    self.run_reference_and_test_comparison()

        def load_obs_dict(self):
            obs_file_name = 'obs_info_dictionary.json'
            obs_json_file = self.load_path_as_file_obj(obs_file_name)
            obs_dic = json.loads(obs_json_file.read())
            obs_json_file.close()
            return obs_dic

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

        def run_reference_and_test_comparison(self):
            reference_data_set = self.parameter.reference_data_set
            reference_data_set = Observation.setup_obs_list_from_parameter(
                reference_data_set, self.obs_dict, self.var)
            test_data_set = self.parameter.test_data_set

            # Member variables are used so when it's obs_vs_model, we know
            # which is which.
            reference_data_set_is_obs = self.is_data_set_obs(reference_data_set)
            test_data_set_is_obs = self.is_data_set_obs(test_data_set)

            # self.reference/self.test are either an obs or model
            for self.reference in reference_data_set:
                for self.test in self.test_data_set:

                    ref = self.determine_obs_or_model(reference_data_set_is_obs,
                                                      self.reference)
                    test = self.determine_obs_or_model(test_data_set_is_obs,
                                                       self.test)

                    self.output_metric.calculate_and_output_metrics(ref, test)

        def is_data_set_obs(self, data_set):
            data_set_is_obs = True
            # If an element of data_set is not in the obs_dict, then
            # data_set is a model.
            for obs in data_set:
                if obs not in self.obs_dict[self.var]:
                    data_set_is_obs = False
                    break
            return data_set_is_obs

        def determine_obs_or_model(self, is_obs, ref_or_test):
            if is_obs:
                return Observation(self.parameter, self.var_name_long,
                                   self.region, ref_or_test, self.obs_dict)
            else:
                return Model(self.parameter, self.var_name_long,
                             self.region, ref_or_test, self.obs_dict)
