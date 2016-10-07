from pcmdi_metrics.PMP.PMPIO import *
from pcmdi_metrics.PMP.DataSet import *


class Model(DataSet):
    def __init__(self, parameter, var_name_long, region,
                 model, obs_dict, sftlf=None):
        super(Model, self).__init__(parameter, var_name_long,
                                    region, obs_dict, sftlf)
        self.obs_or_model = model
        # This is just to make it more clear.
        self.model_file = self.obs_or_model_file
        self.create_model_file()

    def create_model_file(self):
        self.model_file = PMPIO(self.parameter.mod_data_path,
                                self.parameter.filename_template)
        self.model_file.variable = self.var
        self.model_file.model_version = self.obs_or_model
        self.model_file.period = self.parameter.period
        self.model_file.ext = 'nc'
        self.model_file.case_id = self.parameter.case_id
        self.model_file.realization = self.parameter.realization
        self.setup_model_file()

    def setup_model_file(self):
        if self.use_omon(self.obs_dict, self.var):
            regrid_method = self.parameter.regrid_method_ocn
            regrid_tool = self.parameter.regrid_tool
            self.model_file.table = 'Omon'
            self.model_file.realm = 'ocn'
        else:
            regrid_method = self.parameter.regrid_method
            regrid_tool = self.parameter.regrid_tool
            self.model_file.table = 'Amon'
            self.model_file.realm = 'atm'

        self.model_file.set_target_grid(self.parameter.target_grid,
                                        regrid_tool, regrid_method)

    def get(self):
        var_in_file = self.get_var_in_file()

        if self.region is not None:
            region_value = self.region.get('value', None)
            if region_value is not None:
                if self.sftlf[self.obs_or_model]['raw'] is None:
                    self.create_sftlf_model_raw(var_in_file)

                self.model_file.mask = self.sftlf[self.obs_or_model]['raw']
                self.model_file.target_mask = \
                    MV2.not_equal(self.sftlf['target_grid'], region_value)

        try:
            if self.level is None:
                data_model = self.model_file.get_var_from_netcdf(
                    self.var, var_in_file=var_in_file, region=self.region)
            else:
                data_model = self.model_file.get_var_from_netcdf(
                    self.var, var_in_file=var_in_file,
                    level=self.level, region=self.region)
            return data_model

        except Exception as err:
            # TODO do something about success
            success = False
            logging.exception('Failed to get variable %s for the version: %s. Error: %s' % (self.var, self.obs_or_model, err))

    def get_var_in_file(self):
        tweaks = {}
        if hasattr(self.parameter, 'model_tweaks'):
            tweaks = self.parameter.model_tweaks.get(self.obs_or_model, {})
        var_in_file = tweaks.get('variable_mapping', {}).get(self.var, None)

        if var_in_file is None:
            tweaks_all = {}
            if hasattr(self.parameter, 'model_tweaks'):
                tweaks_all = self.parameter.model_tweaks.get(None, {})
            var_in_file = tweaks_all.get(
                'variable_mapping', {}).get(self.var, self.var)

        return var_in_file

    def create_sftlf_model_raw(self, var_in_file):
        if not hasattr(self.parameter, 'generate_sftlf') or \
                        self.parameter.generate_sftlf is False:
            logging.info('Model %s does not have sftlf, skipping region: %s' % (self.obs_or_model, self.region))
            # TODO MAKE success a member variable?
            success = False
        else:
            logging.info('Auto generating sftlf for model %s' % self.model_file())
            if os.path.exists(self.model_file()):
                var_file = cdms2.open(self.model_file())
                var = var_file[var_in_file]
                n = var.rank() - 2  # Minus lat and long
                sft = cdutil.generateLandSeaMask(var(*(slice(0, 1),) * n)) * \
                      100.0
                sft[:] = sft.filled(100.0)
                self.sftlf[self.obs_or_model]['raw'] = sft
                var_file.close()
                logging.info('Auto generated sftlf for model %s' % self.obs_or_model)

    def hash(self):
        return self.model_file.hash()

    def file_path(self):
        return self.model_file()

