import logging
import os
import sys
import json
import collections
from pcmdi_metrics.driver.pmp_parameter import *
from pcmdi_metrics.driver.outputmetrics import *
from pcmdi_metrics.driver.observation import *
from pcmdi_metrics.driver.model import *
from pcmdi_metrics.driver.dataset import *


class RunDiags(object):

        def __init__(self, parameter):
            self.parameter = parameter
            self.obs_dict = {}
            self.regions_dict = {}
            self.var = ''
            self.output_metric = None
            self.region = ''
            self.sftlf = DataSet.create_sftlf(self.parameter)
            self.default_regions = []
            self.regions_specs = {}

        def __call__(self):
            self.run_diags()

        def run_diags(self):
            self.obs_dict = self.load_obs_dict()
            self.regions_dict = self.create_regions_dict()

            for self.var_name_long in self.parameter.vars:
                self.var = self.var_name_long.split('_')[0]

                if self.var not in self.obs_dict:
                    logging.error('Var %s not in obs_dict' % self.var)
                    continue

                self.output_metric = OutputMetrics(
                    self.parameter, self.var_name_long, self.obs_dict, sftlf=self.sftlf)

                for region in self.regions_dict[self.var]:
                    self.region = self.create_region(region)
                    # Runs obs vs obs, obs vs model, or model vs model
                    self.run_reference_and_test_comparison()

        def load_obs_dict(self):
            obs_file_name = 'obs_info_dictionary.json'
            obs_json_file = DataSet.load_path_as_file_obj(obs_file_name)
            obs_dict = json.loads(obs_json_file.read())
            obs_json_file.close()

            if hasattr(self.parameter, 'custom_observations'):
                # Can't use load_path_as_file_obj() b/c might not be in /share/
                cust_obs_json_file = open(self.parameter.custom_observations)
                obs_dict.update(json.load(cust_obs_json_file))
                cust_obs_json_file.close()
            return obs_dict

        def create_regions_dict(self):
            self.load_default_regions_and_regions_specs()

            regions_dict = {}
            for var_name_long in self.parameter.vars:
                var = var_name_long.split('_')[0]
                regions = self.parameter.regions
                region = regions.get(var, self.default_regions)
                if not isinstance(region, (list, tuple)):
                    region = [region]
                if None in region:
                    region.remove(None)
                    for r in self.default_regions:
                        region.insert(0, r)
                regions_dict[var] = region

            return regions_dict

        def load_default_regions_and_regions_specs(self):
            default_regions_file = \
                DataSet.load_path_as_file_obj('default_regions.py')
            execfile(default_regions_file.name)
            default_regions_file.close()
            try:
                self.default_regions = locals()['default_regions']
                self.regions_specs = locals()['regions_specs']
            except KeyError:
                logging.error('Failed to open default_regions.py')

            region_values = self.parameter.regions_values
            region_values.update(getattr(self.parameter, "regions_values", {}))
            # Now need to edit regions_specs
            for region in region_values:
                insert_dict = {'value': region_values[region]}
                if region in self.regions_specs:
                    self.regions_specs[region].update(insert_dict)
                else:
                    self.regions_specs[region] = insert_dict
            self.regions_specs.update(getattr(self.parameter,
                                              "regions_specs", {}))

        def create_region(self, region):
            if isinstance(region, basestring):
                region_name = region
                region = self.regions_specs.get(
                    region_name,
                    self.regions_specs.get(region_name.lower()))
                region['id'] = region_name
            elif region is None:
                # It's okay if region == None
                pass
            else:
                raise Exception('Unknown region: %s' % region)
            return region

        def run_reference_and_test_comparison(self):
            reference_data_set = self.parameter.reference_data_set
            test_data_set = self.parameter.test_data_set

            # Member variables are used so when it's obs_vs_model, we know
            # which is which.
            reference_data_set_is_obs = self.is_data_set_obs(reference_data_set)
            test_data_set_is_obs = self.is_data_set_obs(test_data_set)

            # If reference or test are obs, the data sets themselves need to
            # be modified.
            if reference_data_set_is_obs:
                reference_data_set = Observation.setup_obs_list_from_parameter(
                    reference_data_set, self.obs_dict, self.var)
            if test_data_set_is_obs:
                test_data_set = Observation.setup_obs_list_from_parameter(
                    test_data_set, self.obs_dict, self.var)

            # self.reference/self.test are either an obs or model
            for self.reference in reference_data_set:
                ref = self.determine_obs_or_model(reference_data_set_is_obs,
                                                  self.reference, self.parameter.reference_data_path)

                for self.test in test_data_set:

                    test = self.determine_obs_or_model(test_data_set_is_obs,
                                                       self.test, self.parameter.test_data_path)
                    try:
                        self.output_metric.calculate_and_output_metrics(ref, test)
                    except RuntimeError as e:
                        break

        def is_data_set_obs(self, data_set):
            if 'all' in data_set:
                return True
            data_set_is_obs = True
            # If an element of data_set is not in the obs_dict, then
            # data_set is a model.
            for obs in data_set:
                if obs not in self.obs_dict[self.var]:
                    data_set_is_obs = False
                    break
            return data_set_is_obs

        def determine_obs_or_model(self, is_obs, ref_or_test, data_path):
            if is_obs:
                print 'OBS'
                return Observation(self.parameter, self.var_name_long,
                                   self.region, ref_or_test, self.obs_dict,
                                   data_path, self.sftlf)
            else:
                print 'MODEL'
                return Model(self.parameter, self.var_name_long,
                             self.region, ref_or_test, self.obs_dict,
                             data_path, self.sftlf)
