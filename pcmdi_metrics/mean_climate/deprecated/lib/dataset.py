import abc
import logging
import os
import sys

import cdms2
import cdutil
import xcdat
from six import with_metaclass

from pcmdi_metrics import resources
from pcmdi_metrics.io.base import Base


class DataSet(with_metaclass(abc.ABCMeta, object)):
    """Abstract parent of the Observation of Model classes."""

    def __init__(self, parameter, var_name_long, region, obs_dict, data_path, sftlf):
        self.parameter = parameter
        self.var_name_long = var_name_long
        self.region = region
        self.obs_dict = obs_dict
        self.data_path = data_path

        self.var = var_name_long.split("_")[0]
        self.level = self.calculate_level_from_var(var_name_long)

        self.sftlf = sftlf

    def get_sftlf(self):
        """Returns the sftlf attribute."""
        return self.sftlf

    def __call__(self):
        return self.get()

    @staticmethod
    def calculate_level_from_var(var):
        """Get the level from the var string, where it's var_LEVEL"""
        var_split_name = var.split("_")
        if len(var_split_name) > 1:
            level = float(var_split_name[-1]) * 100
        else:
            level = None
        return level

    def setup_target_grid(self, obs_or_model_file):
        """Call the set_target_grid function for
        obs_or_model_file, which is of type Base."""
        if self.use_omon(self.obs_dict, self.var):
            regrid_method = self.parameter.regrid_method_ocn
            regrid_tool = self.parameter.regrid_tool_ocn
            obs_or_model_file.table = "Omon"
            obs_or_model_file.realm = "ocn"
        else:
            regrid_method = self.parameter.regrid_method
            regrid_tool = self.parameter.regrid_tool
            obs_or_model_file.table = "Amon"
            obs_or_model_file.realm = "atm"

        obs_or_model_file.set_target_grid(
            self.parameter.target_grid, regrid_tool, regrid_method
        )

    @staticmethod
    def use_omon(obs_dict, var):
        """For the given variable and obs_dict, do we use Omon?"""
        obs_default = obs_dict[var][obs_dict[var]["default"]]
        return obs_default["CMIP_CMOR_TABLE"] == "Omon"

    @staticmethod
    def create_sftlf(parameter):
        """Create the sftlf file from the parameter."""
        sftlf = {}

        print('jwlee-test_create_sftlf, parameter.test_data_set:', parameter.test_data_set)
        for test in parameter.test_data_set:
            tmp_name = getattr(parameter, "sftlf_filename_template")
            if tmp_name is None:  # Not defined from commandline or param file
                tmp_name = parameter.filename_template
            print('jwlee-test_create_sftlf, tmp_name:', tmp_name)
            sft = Base(parameter.test_data_path, tmp_name)
            sft.model_version = test
            sft.table = "fx"
            sft.realm = "atmos"
            sft.period = getattr(parameter, "period", "")
            sft.ext = "nc"
            sft.case_id = getattr(parameter, "case_id", "")
            sft.target_grid = None
            sft.realization = "r0i0p0"
            DataSet.apply_custom_keys(sft, parameter.custom_keys, "sftlf")
            try:
                print('jwlee-test_create_sftlf, chk1')
                sftlf[test] = {"raw": sft.get("sftlf")}
                print('jwlee-test_create_sftlf, chk1-2')
                sftlf[test]["filename"] = os.path.basename(sft())
                print('jwlee-test_create_sftlf, chk1-3')
                sftlf[test]["md5"] = sft.hash()
                print('jwlee-test_create_sftlf, chk1-4')
            except Exception:
                print('jwlee-test_create_sftlf, chk2')
                sftlf[test] = {"raw": None}
                sftlf[test]["filename"] = None
                sftlf[test]["md5"] = None
        print('jwlee-test-target_grid-create')
        if parameter.target_grid == "2.5x2.5":
            t_grid_cdms2 = cdms2.createUniformGrid(-88.875, 72, 2.5, 0, 144, 2.5)
            t_grid = xcdat.create_uniform_grid(-88.875, 88.625, 2.5, 0, 357.5, 2.5)
        else:
            t_grid = parameter.target_grid
        print('jwlee-test-target_grid-create done')
        print('jwlee-test-target_grid-create t_grid:', t_grid)

        # sft = cdutil.generateLandSeaMask(t_grid)
        sft = cdutil.generateLandSeaMask(t_grid_cdms2)
        sft[:] = sft.filled(1.0) * 100.0
        sftlf["target_grid"] = sft
        print('jwlee-test-target_grid, type(sft), sft.shape:', type(sft), sft.shape)

        print("jwlee-test_create_sftlf, sftlf[test]['raw']:", sftlf[test]['raw'])

        return sftlf

    @staticmethod
    def apply_custom_keys(obj, custom_dict, var):
        """Apply the all of the keys in custom_dict that are var to obj."""
        for k, v in custom_dict.items():
            key = custom_dict[k]
            setattr(obj, k, key.get(var, key.get(None, "")))

    @abc.abstractmethod
    def get(self):
        """Calls the get function on the Base object."""
        raise NotImplementedError()

    @staticmethod
    def load_path_as_file_obj(name):
        """Returns a File object for the file named name."""
        egg_pth = resources.resource_path()
        file_path = os.path.join(egg_pth, name)
        opened_file = None
        try:
            opened_file = open(file_path)
        except IOError:
            logging.getLogger("pcmdi_metrics").error(
                "%s could not be loaded!" % file_path
            )
        except Exception:
            logging.getLogger("pcmdi_metrics").error(
                "Unexpected error while opening file: " + sys.exc_info()[0]
            )
        return opened_file

    @abc.abstractmethod
    def hash(self):
        """Calls the hash function on the Base object."""
        raise NotImplementedError()

    def file_path(self):
        """Calls the __call__() function on the Base object."""
        raise NotImplementedError()
