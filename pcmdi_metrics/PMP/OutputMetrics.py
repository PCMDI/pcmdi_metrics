import collections
import sys
from pcmdi_metrics.PMP.PMPIO import *


class OutputMetrics(object):

    def __init__(self, parameter, var_name_long):
        self.parameter = parameter
        self.var_name_long = var_name_long

        self.var = var_name_long.split('_')[0]
        self.metrics_dictionary = {}
        string_template = "%(var)%(level)_%(targetGridName)_" +\
                          "%(regridTool)_%(regridMethod)_metrics"
        self.out_file = PMPIO(self.parameter.metrics_output_path,
                              string_template)
        self.setup_metrics_dictionary()

    def setup_metrics_dictionary(self):
        self.metrics_dictionary = collections.OrderedDict()
        self.metrics_dictionary["RESULTS"] = collections.OrderedDict()
        self.metrics_dictionary["DISCLAIMER"] = self.open_disclaimer()

        self.metrics_dictionary["Variable"] = {}
        self.metrics_dictionary["Variable"]["id"] = self.var
        self.metrics_dictionary["References"] = {}
        self.metrics_dictionary["RegionalMasking"] = {}

        level = self.calculate_level_from_var(self.var_name_long)
        if level is not None:
            self.metrics_dictionary["Variable"]["level"] = level

    def open_disclaimer(self):
        f = self.load_path_as_file_obj('disclaimer.txt')
        contents = f.read()
        f.close()
        return contents

    def set_target_grid(self, regrid_tool, regrid_method):
        self.out_file.set_target_grid(self.parameter.target_grid,
                                      regrid_tool, regrid_method)

    def set_var(self, var):
        self.out_file.var = var

    def set_realm(self, realm):
        self.out_file.realm = realm

    def set_table(self, table):
        self.out_file.table = table

    def set_case_id(self, case_id):
        self.out_file.case_id = case_id

    def set_simulation_desc(self, model, obs_dict):
        # lines 564 - 617
        # need to use model.model_version
        pass

    def write_out_file(self):
        # line 736 - 744
        pass

    def output_interpolated_model_climatologies(self):
        # lines 699 - 721
        pass

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


