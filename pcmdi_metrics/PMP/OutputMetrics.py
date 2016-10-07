import collections
import sys
from pcmdi_metrics.PMP.PMPIO import *
from pcmdi_metrics.PMP.metrics.mean_climate_metrics_calculations import *
from pcmdi_metrics.PMP.Observation import *
from pcmdi_metrics.PMP.DataSet import DataSet


class OutputMetrics(object):

    def __init__(self, parameter, var_name_long, obs_dict):
        self.parameter = parameter
        self.var_name_long = var_name_long
        self.obs_dict = obs_dict
        self.var = var_name_long.split('_')[0]

        self.metrics_def_dictionary = {}
        self.metrics_dictionary = {}

        string_template = "%(var)%(level)_%(target_grid_name)_" +\
                          "%(regrid_tool)_%(regrid_method)_metrics"
        self.out_file = PMPIO(self.parameter.metrics_output_path,
                              string_template)

        self.sftlf = DataSet.create_sftlf(self.parameter)
        self.setup_metrics_dictionary()

        self.regrid_method = ''
        self.regrid_tool = ''
        self.table_realm = ''
        self.realm = ''
        self.setup_regrid_and_realm_vars()
        self.setup_out_file()

    def setup_metrics_dictionary(self):
        self.metrics_def_dictionary = collections.OrderedDict()
        self.metrics_dictionary = collections.OrderedDict()
        self.metrics_dictionary["RESULTS"] = collections.OrderedDict()
        self.metrics_dictionary["DISCLAIMER"] = self.open_disclaimer()

        self.metrics_dictionary["Variable"] = {}
        self.metrics_dictionary["Variable"]["id"] = self.var
        self.metrics_dictionary["References"] = {}
        self.metrics_dictionary["RegionalMasking"] = {}

        level = DataSet.calculate_level_from_var(self.var_name_long)
        if level is not None:
            self.metrics_dictionary["Variable"]["level"] = level

    def open_disclaimer(self):
        f = DataSet.load_path_as_file_obj('disclaimer.txt')
        contents = f.read()
        f.close()
        return contents

    def setup_regrid_and_realm_vars(self):
        if DataSet.use_omon(self.obs_dict, self.var):
            self.regrid_method = self.parameter.regrid_method_ocn
            self.regrid_tool = self.parameter.regrid_tool_ocn
            self.table_realm = 'Omon'
            self.realm = "ocn"
        else:
            self.regrid_method = self.parameter.regrid_method
            self.regrid_tool = self.parameter.regrid_tool
            self.table_realm = 'Amon'
            self.realm = "atm"

    def setup_out_file(self):
        self.out_file.set_target_grid(
            self.parameter.target_grid, self.regrid_tool, self.regrid_method)
        self.out_file.variable = self.var
        self.out_file.realm = self.realm
        self.out_file.table = self.table_realm
        self.out_file.case_id = self.parameter.case_id

    def calculate_and_output_metrics(self, ref, test):
        ref_data = ref()
        test_data = test()

        if ref_data.shape != test_data.shape:
            raise RuntimeError('Two data sets have different shapes. %s vs %s' % (ref_data.shape, test_data.shape))

        self.set_simulation_desc(ref, test)

        self.metrics_dictionary["RESULTS"][ref.obs_or_model] = \
            self.metrics_dictionary["RESULTS"].get(test.obs_or_model, {})
        self.metrics_dictionary["RESULTS"][test.obs_or_model][ref.obs_or_model] = \
            {'source': self.obs_dict[self.var][ref.obs_or_model]}
        parameter_realization = self.metrics_dictionary["RESULTS"][test.obs_or_model][ref.obs_or_model].\
            get(self.parameter.realization, {})
        self.metrics_dictionary["RESULTS"][test.obs_or_model]\
            [ref.obs_or_model][self.parameter.realization] = \
            parameter_realization

        if not self.parameter.dry_run:

            pr_rgn = compute_metrics(self.var_name_long, test_data, ref_data)
            self.metrics_def_dictionary.update(
                compute_metrics(self.var_name_long, test_data, ref_data))
            if hasattr(self.parameter, 'compute_custom_metrics'):
                pr_rgn.update(
                    self.parameter.compute_custom_metrics(test_data, ref_data))
                try:
                    self.metrics_def_dictionary.update(
                        self.parameter.compute_custom_metrics(
                            self.var_name_long, None, None))
                except:
                    self.metrics_def_dictionary.update(
                        {'custom':
                             self.parameter.compute_custom_metrics.__doc__})

            parameter_realization[self.get_region_name()] = collections.OrderedDict(
                (k, parameter_realization[k]) for k in sorted(parameter_realization.keys())
            )
            self.metrics_dictionary['RESULTS'][test.obs_or_model]\
                [ref.obs_or_model][self.parameter.realization] = \
                self.parameter_realization

        if self.check_save_mod_clim(ref):
            self.output_interpolated_model_climatologies(test)

        self.metrics_dictionary['METRICS'] = self.metrics_def_dictionary

        if not self.parameter.dry_run:
            self.out_file.write(self.metrics_dictionary, mode='w', indent=4,
                                seperators=(',', ': '))
            self.out_file.write(self.metrics_dictionary, mode='w', type='txt')

    def set_simulation_desc(self, ref, test):
        test_data = test()

        if "SimulationDescription" not in \
                self.metrics_dictionary["RESULTS"][test.obs_or_model]:

            if isinstance(self.obs_dict[self.var][ref.obs_or_model], (str, unicode)):
                obs_var_ref = self.obs_dict[self.var][self.obs_dict[self.var][ref.obs_or_model]]
            else:
                obs_var_ref = self.obs_dict[self.var][ref.obs_or_model]

            descr = {"MIPTable": obs_var_ref["CMIP_CMOR_TABLE"],
                     "Model": ref.obs_or_model,
                     }
            sim_descr_mapping = {
                "ModelActivity": "project_id",
                "ModellingGroup": "institute_id",
                "Experiment": "experiment",
                "ModelFreeSpace": "ModelFreeSpace",
                "Realization": "realization",
                "creation_date": "creation_date",
            }
            sim_descr_mapping.update(
                getattr(self.parameter, "simulation_description_mapping",{}))

            for att in sim_descr_mapping.keys():
                nm = sim_descr_mapping[att]
                if not isinstance(nm, (list, tuple)):
                    nm = ["%s", nm]
                fmt = nm[0]
                vals = []
                for a in nm[1:]:
                    # First trying from parameter file
                    if hasattr(self.parameter, a):
                        vals.append(getattr(self.parameter, a))
                    # Now fall back on file...
                    else:
                        f = cdms2.open(test.get_file_path())
                        if hasattr(f, a):
                            try:
                                vals.append(float(getattr(f,a)))
                            except:
                                vals.append(getattr(f, a))
                        # Ok couldn't find it anywhere
                        # setting to N/A
                        else:
                            vals.append("N/A")
                        f.close()
                descr[att] = fmt % tuple(vals)

            self.metrics_dictionary["RESULTS"][test.obs_or_model]["units"] = \
                getattr(test_data,"units","N/A")
            self.metrics_dictionary["RESULTS"][test.obs_or_model]\
                ["SimulationDescription"] = descr

            self.metrics_dictionary["RESULTS"][test.obs_or_model][
                "InputClimatologyFileName"] = \
                os.path.basename(test.file_path())
            self.metrics_dictionary["RESULTS"][test.obs_or_model][
                "InputClimatologyMD5"] = test.hash()
            # Not just global
            if len(self.regions_dict[self.var]) > 1:
                self.metrics_dictionary["RESULTS"][test.obs_or_model][
                    "InputRegionFileName"] = \
                    self.sftlf[test.obs_or_model]["filename"]
                self.metrics_dictionary["RESULTS"][test.obs_or_model][
                    "InputRegionMD5"] = \
                    self.sftlf[test.obs_or_model]["md5"]

    def output_interpolated_model_climatologies(self, test):
        region_name = self.get_region_name()
        pth = os.path.join(self.parameter.model_clims_interpolated_output,
                           region_name)
        clim_file = PMPIO(pth, self.parameter.filename_output_template)
        clim_file.level = self.out_file.level
        clim_file.model_version = test.obs_or_model
        clim_file.table = self.table_realm
        clim_file.period = self.parameter.period
        clim_file.case_id = self.parameter.case_id
        clim_file.set_target_grid(
            self.parameter.targetGrid,
            self.regrid_tool,
            self.regrid_method)
        clim_file.variable = self.var
        clim_file.region = region_name
        clim_file.realization = self.parameter.realization
        DataSet.apply_custom_keys(clim_file,
                                  self.parameter.custom_keys, self.var)
        clim_file.write(test(), type="nc", id=self.var)

    def get_region_name(self):
        # region is both in ref and test
        region_name = self.ref.region
        if self.ref.region is None:
            region_name = 'global'
        return region_name

    def check_save_mod_clim(self, ref):
        # Since we are only saving once per reference data set (it's always
        # the same after), we need to check if ref is the first value from the
        # parameter, hence we have ref.obs_or_model == reference_data_set[0]
        reference_data_set = self.parameter.reference_data_set
        reference_data_set = Observation.setup_obs_list_from_parameter(
                reference_data_set ,self.obs_dict, self.var)

        return not self.parameter.dry_run and \
               hasattr(self.parameter, 'save_mod_clim') and \
               self.parameter.save_mod_clim is True and \
               ref.obs_or_model == reference_data_set[0]
