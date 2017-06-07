#!/usr/bin/env python
import logging
import json
from pcmdi_metrics.driver.outputmetrics import OutputMetrics
from pcmdi_metrics.driver.observation import Observation
from pcmdi_metrics.driver.model import Model
import pcmdi_metrics.driver.dataset
import pcmdi_metrics.driver.pmp_parser
from pcmdi_metrics import LOG_LEVEL


class PMPDriver(object):

    def __init__(self, parameter):
        logging.basicConfig(level=LOG_LEVEL)

        self.parameter = parameter
        self.obs_dict = {}
        self.regions_dict = {}
        self.var = ''
        self.output_metric = None
        self.region = ''
        self.sftlf = pcmdi_metrics.driver.dataset.DataSet.create_sftlf(self.parameter)
        self.default_regions = []
        self.regions_specs = {}

    def __call__(self):
        self.run_diags()

    def run_diags(self):
        ''' Runs the diagnostics. What did you think it did? '''
        self.obs_dict = self.load_obs_dict()
        self.regions_dict = self.create_regions_dict()

        for self.var_name_long in self.parameter.vars:
            self.var = self.var_name_long.split('_')[0]

            if self.var not in self.obs_dict:
                logging.error('Variable %s not in obs_dict' % self.var)
                continue

            self.output_metric = OutputMetrics(self.parameter, self.var_name_long,
                                               self.obs_dict, sftlf=self.sftlf)

            for region in self.regions_dict[self.var]:
                self.region = self.create_region(region)
                # Need to add the region to the output dict now b/c
                # otherwise if done later, sometimes it's not added due to
                # premature break in the for loops for reference and test.
                self.output_metric.add_region(self.region)
                # Runs obs vs obs, obs vs model, or model vs model
                self.run_reference_and_test_comparison()
            self.output_metric.write_on_exit()

    def load_obs_dict(self):
        ''' Loads obs_info_dictionary.json and appends
        custom_observations from the parameter file if needed. '''
        obs_file_name = 'obs_info_dictionary.json'
        obs_json_file = pcmdi_metrics.driver.dataset.DataSet.load_path_as_file_obj(obs_file_name)
        obs_dict = json.loads(obs_json_file.read())
        obs_json_file.close()

        if hasattr(self.parameter, 'custom_observations'):
            # Can't use load_path_as_file_obj() b/c might not be in /share/
            cust_obs_json_file = open(self.parameter.custom_observations)
            obs_dict.update(json.load(cust_obs_json_file))
            cust_obs_json_file.close()
        return obs_dict

    def create_regions_dict(self):
        ''' Creates a dict from self.default_regions. '''
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
        ''' Gets the default_regions dict and regions_specs dict
        from default_regions.py and stores them as attributes. '''
        default_regions_file = \
            pcmdi_metrics.driver.dataset.DataSet.load_path_as_file_obj('default_regions.py')
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
        ''' From the argument region, it gets that region from self.regions_specs
        (which itself is loaded from default_regions.py) '''
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
        '''  Does the (obs or model) vs (obs or model) comparison. '''
        reference_data_set = self.parameter.reference_data_set
        test_data_set = self.parameter.test_data_set

        reference_data_set_is_obs = self.is_data_set_obs(reference_data_set)
        test_data_set_is_obs = self.is_data_set_obs(test_data_set)

        # If either the reference or test are obs, the data sets
        # themselves need to be modified.
        if reference_data_set_is_obs:
            reference_data_set = Observation.setup_obs_list_from_parameter(
                reference_data_set, self.obs_dict, self.var)
        if test_data_set_is_obs:
            test_data_set = Observation.setup_obs_list_from_parameter(
                test_data_set, self.obs_dict, self.var)

        # self.reference/self.test are either an obs or model
        for reference in reference_data_set:
            try:
                ref = self.determine_obs_or_model(reference_data_set_is_obs,
                                                  reference, self.parameter.reference_data_path)
            # TODO Make this a custom exception. This exception is for
            # when a model doesn't have sftlf for a given region
            except RuntimeError:
                continue

            for test in test_data_set:
                try:
                    tst = self.determine_obs_or_model(test_data_set_is_obs,
                                                      test, self.parameter.test_data_path)
                # TODO Make this a custom exception. This exception is for
                # when a model doesn't have sftlf for a given region
                except RuntimeError:
                    continue

                try:
                    self.output_metric.calculate_and_output_metrics(ref, tst)
                except RuntimeError:
                    break

    def is_data_set_obs(self, data_set):
        ''' Is data_set (which is either a test or reference) an obs? '''
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
        ''' Actually create Observation or Module object
        based on if ref_or_test is an obs or model. '''
        if is_obs:
            logging.info('%s is an obs' % ref_or_test)
            return Observation(self.parameter, self.var_name_long, self.region,
                               ref_or_test, self.obs_dict, data_path, self.sftlf)
        else:
            logging.info('%s is a model' % ref_or_test)
            return Model(self.parameter, self.var_name_long, self.region,
                         ref_or_test, self.obs_dict, data_path, self.sftlf)


parser = pcmdi_metrics.driver.pmp_parser.PMPParser()
parameter = parser.get_parameter()
driver = PMPDriver(parameter)
driver.run_diags()
