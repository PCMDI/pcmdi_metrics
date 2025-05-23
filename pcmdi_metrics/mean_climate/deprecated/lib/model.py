import logging
import os

import cdms2
import cdutil
import MV2

from pcmdi_metrics import LOG_LEVEL
from pcmdi_metrics.io.base import Base
from pcmdi_metrics.mean_climate.lib.dataset import DataSet


class Model(DataSet):
    """Handles all the computation (setting masking, target grid, etc)
    and some file I/O related to models."""

    def __init__(
        self, parameter, var_name_long, region, model, obs_dict, data_path, sftlf
    ):
        super(Model, self).__init__(
            parameter, var_name_long, region, obs_dict, data_path, sftlf
        )
        logging.getLogger("pcmdi_metrics").setLevel(LOG_LEVEL)

        self._model_file = None
        self.var_in_file = None
        self.obs_or_model = model
        self.create_model_file()
        self.setup_target_grid(self._model_file)
        self.setup_target_mask()

    def create_model_file(self):
        """Creates an object that will eventually output the netCDF file."""
        self._model_file = Base(self.data_path, self.parameter.filename_template)
        self._model_file.variable = self.var
        self._model_file.model_version = self.obs_or_model
        self._model_file.period = self.parameter.period
        self._model_file.ext = "nc"
        self._model_file.case_id = self.parameter.case_id
        self._model_file.realization = self.parameter.realization
        self.apply_custom_keys(self._model_file, self.parameter.custom_keys, self.var)

    def setup_target_mask(self):
        """Sets the mask and target_mask attribute of self._model_file"""
        self.var_in_file = self.get_var_in_file()

        print("jwlee-test-setup_target_mask, self.var_in_file:", self.var_in_file)
        print("jwlee-test-setup_target_mask, self.region:", self.region)
        print("jwlee-test-setup_target_mask, self.obs_or_model:", self.obs_or_model)

        if self.region is not None:
            region_value = self.region.get("value", None)
            print("jwlee-test-setup_target_mask, region_value:", region_value)
            if region_value is not None:
                print("jwlee-test-setup_target_mask, self.sftlf:", self.sftlf)
                print(
                    "jwlee-test-setup_target_mask, self.sftlf[self.obs_or_model]:",
                    self.sftlf[self.obs_or_model],
                )
                print(
                    'jwlee-test-setup_target_mask, self.sftlf[self.obs_or_model]["raw"]:',
                    self.sftlf[self.obs_or_model]["raw"],
                )
                if self.sftlf[self.obs_or_model]["raw"] is None:
                    self.create_sftlf_model_raw(self.var_in_file)

                self._model_file.mask = self.sftlf[self.obs_or_model]["raw"]
                self._model_file.target_mask = MV2.not_equal(
                    self.sftlf["target_grid"], region_value
                )

    def get(self):
        """Gets the variable based on the region and level (if given) for
        the file from data_path, which is defined in the initalizer."""
        print(
            "jwlee-test-get: self.var_in_file, self.region:",
            self.var_in_file,
            self.region,
        )
        try:
            if self.level is None:
                data_model = self._model_file.get(
                    self.var, var_in_file=self.var_in_file, region=self.region
                )
            else:
                data_model = self._model_file.get(
                    self.var,
                    var_in_file=self.var_in_file,
                    level=self.level,
                    region=self.region,
                )

            return data_model

        except Exception as e:
            msg = "Failed to get variables %s for versions: %s, error: %s"
            logging.getLogger("pcmdi_metrics").error(
                msg % (self.var, self.obs_or_model, e)
            )
            raise RuntimeError("Need to skip model: %s" % self.obs_or_model)

    def get_var_in_file(self):
        """Based off the model_tweaks parameter, get the variable mapping."""
        tweaks = {}
        tweaks_all = {}
        if hasattr(self.parameter, "model_tweaks"):
            tweaks = self.parameter.model_tweaks.get(self.obs_or_model, {})
            tweaks_all = self.parameter.model_tweaks.get(None, {})
        var_in_file = tweaks.get("variable_mapping", {}).get(self.var, None)

        if var_in_file is None:
            if hasattr(self.parameter, "model_tweaks"):
                tweaks_all = self.parameter.model_tweaks.get(None, {})
            var_in_file = tweaks_all.get("variable_mapping", {}).get(self.var, self.var)

        return var_in_file

    def create_sftlf_model_raw(self, var_in_file):
        """For the self.obs_or_model from the initializer, create a landSeaMask
        from cdutil for self.sftlf[self.obs_or_model]['raw'] value."""
        if (
            not hasattr(self.parameter, "generate_sftlf")
            or self.parameter.generate_sftlf is False
        ):
            logging.getLogger("pcmdi_metrics").info(
                "Model %s does not have sftlf, skipping region: %s"
                % (self.obs_or_model, self.region)
            )
            raise RuntimeError(
                "Model %s does not have sftlf, skipping region: %s"
                % (self.obs_or_model, self.region)
            )

        else:
            logging.getLogger("pcmdi_metrics").info(
                "Auto generating sftlf for model %s" % self._model_file()
            )
            if os.path.exists(self._model_file()):
                var_file = cdms2.open(self._model_file())
                var = var_file[var_in_file]
                n = var.rank() - 2  # Minus lat and long
                sft = cdutil.generateLandSeaMask(var(*(slice(0, 1),) * n)) * 100.0
                sft[:] = sft.filled(100.0)
                self.sftlf[self.obs_or_model]["raw"] = sft
                var_file.close()
                logging.getLogger("pcmdi_metrics").info(
                    "Auto generated sftlf for model %s" % self.obs_or_model
                )

    def hash(self):
        """Return a hash of the file."""
        return self._model_file.hash()

    def file_path(self):
        """Return the path of the file."""
        return self._model_file()
