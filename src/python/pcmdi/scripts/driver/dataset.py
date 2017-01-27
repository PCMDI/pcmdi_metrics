import abc
import os
import sys
import logging
import cdutil
import cdms2
import pcmdi_metrics.io.base


class DataSet(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parameter, var_name_long, region,
                 obs_dict, data_path, sftlf):
        self.parameter = parameter
        self.var_name_long = var_name_long
        self.region = region
        self.obs_dict = obs_dict
        self.data_path = data_path

        self.var = var_name_long.split('_')[0]
        self.level = self.calculate_level_from_var(var_name_long)

        self.sftlf = sftlf

    def get_sftlf(self):
        return self.sftlf

    def __call__(self):
        return self.get()

    @staticmethod
    def calculate_level_from_var(var):
        var_split_name = var.split('_')
        if len(var_split_name) > 1:
            level = float(var_split_name[-1]) * 100
        else:
            level = None
        return level

    def setup_target_grid(self, obs_or_model_file):
        if self.use_omon(self.obs_dict, self.var):
            regrid_method = self.parameter.regrid_method_ocn
            regrid_tool = self.parameter.regrid_tool_ocn
            obs_or_model_file.table = 'Omon'
            obs_or_model_file.realm = 'ocn'
        else:
            regrid_method = self.parameter.regrid_method
            regrid_tool = self.parameter.regrid_tool
            obs_or_model_file.table = 'Amon'
            obs_or_model_file.realm = 'atm'

        obs_or_model_file.set_target_grid(self.parameter.target_grid,
                                          regrid_tool, regrid_method)

    @staticmethod
    def use_omon(obs_dict, var):
        obs_default = obs_dict[var][obs_dict[var]["default"]]
        return obs_default["CMIP_CMOR_TABLE"] == 'Omon'

    @staticmethod
    def create_sftlf(parameter):
        sftlf = {}

        for test in parameter.test_data_set:
            sft = pcmdi_metrics.io.base.Base(parameter.test_data_path,
                                                getattr(parameter, "sftlf_filename_template",
                                                        parameter.filename_template))
            sft.model_version = test
            sft.table = "fx"
            sft.realm = "atmos"
            sft.period = getattr(parameter, 'period', '')
            sft.ext = "nc"
            sft.case_id = getattr(parameter, 'case_id', '')
            sft.target_grid = None
            sft.realization = "r0i0p0"
            DataSet.apply_custom_keys(sft, parameter.custom_keys, "sftlf")
            try:
                sftlf[test] = {"raw": sft.get("sftlf")}
                sftlf[test]["filename"] = os.path.basename(sft())
                sftlf[test]["md5"] = sft.hash()
            except:
                sftlf[test] = {"raw": None}
                sftlf[test]["filename"] = None
                sftlf[test]["md5"] = None
        if parameter.target_grid == "2.5x2.5":
            t_grid = cdms2.createUniformGrid(-88.875, 72, 2.5, 0, 144, 2.5)
        else:
            t_grid = parameter.target_grid

        sft = cdutil.generateLandSeaMask(t_grid)
        sft[:] = sft.filled(1.0) * 100.0
        sftlf["target_grid"] = sft

        return sftlf

    @staticmethod
    def apply_custom_keys(obj, custom_dict, var):
        for k, v in custom_dict.iteritems():
            key = custom_dict[k]
            setattr(obj, k, key.get(var, key.get(None, "")))

    @abc.abstractmethod
    def get(self):
        """Calls the get function on the Base object."""
        raise NotImplementedError()

    @staticmethod
    def load_path_as_file_obj(name):
        file_path = sys.prefix + '/share/pmp/' + name
        opened_file = None
        try:
            opened_file = open(file_path)
        except IOError:
            logging.error('%s could not be loaded!' % file_path)
        except:
            logging.error('Unexpected error while opening file: '
                          + sys.exc_info()[0])
        return opened_file

    @abc.abstractmethod
    def hash(self):
        """Calls the hash function on the Base object."""
        raise NotImplementedError()

    def file_path(self):
        """Calls the __call__() function on the Base object."""
        raise NotImplementedError()
