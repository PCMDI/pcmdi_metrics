from pcmdi_metrics.PMP.PMPIO import *


class Model(object):
    def __init__(self, parameter, var_name_long, region, model, obs_dict):
        self.parameter = parameter
        self.parameter = parameter
        self.level = self.calculate_level_from_var(var_name_long)
        self.var = var_name_long.split('_')[0]
        self.region = region
        self.model = model
        self.obs_dict = obs_dict
        self.model_file = None
        self.sftlf = self.create_sftlf(self.parameter)
        self.create_model_file()

    def __call__(self, *args, **kwargs):
        self.get()

    @staticmethod
    def calculate_level_from_var(var):
        var_split_name = var.split('_')
        if len(var_split_name) > 1:
            level = float(var_split_name[-1]) * 100
        else:
            level = None
        return level

    @staticmethod
    def create_sftlf(parameter):
        sftlf = {}
        # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
        for model_version in parameter.model_versions:
            sft = PMPIO(
                parameter.mod_data_path,
                getattr(
                    parameter,
                    "sftlf_filename_template",
                    parameter.filename_template))
            sft.model_version = model_version
            sft.table = "fx"
            sft.realm = "atmos"
            sft.period = parameter.period
            sft.ext = "nc"
            sft.case_id = parameter.case_id
            sft.targetGrid = None
            sft.realization = "r0i0p0"
            #applyCustomKeys(sft, parameter.custom_keys, "sftlf")
            try:
                sftlf[model_version] = {"raw": sft.get("sftlf")}
                sftlf[model_version]["filename"] = os.path.basename(sft())
                sftlf[model_version]["md5"] = sft.hash()
            except:
                # Hum no sftlf...
                sftlf[model_version] = {"raw": None}
                sftlf[model_version]["filename"] = None
                sftlf[model_version]["md5"] = None
        if parameter.targetGrid == "2.5x2.5":
            tGrid = cdms2.createUniformGrid(-88.875, 72, 2.5, 0, 144, 2.5)
        else:
            tGrid = parameter.targetGrid

        sft = cdutil.generateLandSeaMask(tGrid)
        sft[:] = sft.filled(1.) * 100.0
        sftlf["targetGrid"] = sft

        return sftlf

    def create_model_file(self):
        self.model_file = PMPIO(self.parameter.mod_data_path,
                                self.parameter.filename_template)
        self.model_file.model_version = self.model
        self.model_file.period = self.parameter.period
        self.model_file.ext = 'nc'
        self.model_file.case_id = self.parameter.case_id
        self.model_file.realization = self.parameter.realization
        self.setup_model_file(self.model_file)

    def setup_model_file(self):
        regrid_method = ''
        regrid_tool = ''

        if self.use_omon():
            regrid_method = self.parameter.regrid_method_ocn
            regrid_tool = self.regrid_tool_ocn.regrid_tool
            self.model_file.table = 'Omon'
            self.model_file.realm = 'ocn'
        else:
            regrid_method = self.parameter.regrid_method
            regrid_tool = self.parameter.regrid_tool
            self.model_file.table = 'Amon'
            self.model_file.realm = 'atm'

        self.model_file.set_target_grid(self.parameter.target_grid,
                                        regrid_tool,
                                        regrid_method)

    def use_omon(self):
        return \
            self.obs_dict[self.var][self.obs_dict[self.var]["default"]]\
                ["CMIP_CMOR_TABLE"] == 'Omon'

    def get(self):
        var_in_file = self.get_var_in_file()

        if self.region is not None:
            region_value = self.region.get('value', None)
            if region_value is not None:
                if self.sftlf[self.model]['raw'] is None:
                    self.create_sftlf_model_raw(var_in_file)

                self.model_file.mask = self.sftlf[self.model]['raw']
                self.model_file.target_mask = MV2.not_equal(self.sftlf['targetGrid'], region_value)

        try:
            if self.level is None:
                data_model = self.model_file.get(self.var,
                                                 var_in_file=var_in_file,
                                                 region=self.region)
            else:
                data_model = self.model_file.get(self.var,
                                                 var_in_file=var_in_file,
                                                 level=self.level,
                                                 region=self.region)
            return data_model
        except Exception as err:
            #TODO do something about success
            success = False
            logging.exception('Failed to get variable %s for the version: %s. Error: %s' % (self.var, self.model, err))


    def get_var_in_file(self):
        tweaks = {}
        if hasattr(self.parameter, 'model_tweaks'):
            tweaks = self.parameter.model_tweaks.get(self.model, {})
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
            logging.info('Model %s does not have sftlf, skipping region: %s' % (self.model, self.region))
            # TODO MAKE success a member variable?
            success = False
        else:
            self.model_file.variable = self.var
            logging.info('Auto generating sftlf for model %s' % self.model())
            if os.path.exists(self.model_file()):
                var_file = cdms2.open(self.model_file())
                var = var_file[var_in_file]
                N = var.rank() - 2  # Minus lat and long
                sft = cdutil.generateLandSeaMask(var(*(slice(0, 1),) * N)) * 100.0
                sft[:] = sft.filled(100.0)
                self.sftlf[self.model]['raw'] = sft
                var_file.close()
                logging.info('Auto generated sftlf for model %s' % self.model)
