import logging
import os
import sys
import json
import collections
from pcmdi_metrics.PMP.PMPDriver import *
from pcmdi_metrics.PMP.PMPParameter import *


class PMPDriverRunDiags(object):

        def __init__(self, parameter):
            self.parameter = parameter

        def run_diags(self):
            for self.var_name_long in self.parameter.vars:
                self.var = self.var_name_long
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

        def load_obs_dic(self):
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

