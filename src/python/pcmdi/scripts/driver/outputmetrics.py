import collections
import logging
import os
import cdms2
import pcmdi_metrics
from pcmdi_metrics.io.base import Base
from pcmdi_metrics.driver.observation import Observation
from pcmdi_metrics.driver.dataset import DataSet
from pcmdi_metrics import LOG_LEVEL


class OutputMetrics(object):

    def __init__(self, parameter, var_name_long, obs_dict, sftlf):
        logging.getLogger("pcmdi_metrics").setLevel(LOG_LEVEL)
        self.parameter = parameter
        self.var_name_long = var_name_long
        self.obs_dict = obs_dict
        self.var = var_name_long.split('_')[0]
        self.sftlf = sftlf

        self.metrics_def_dictionary = {}
        self.metrics_dictionary = {}

        string_template = "%(variable)%(level)_%(target_grid_name)_" +\
                          "%(regrid_tool)_%(regrid_method)_metrics"
        self.out_file = Base(self.parameter.metrics_output_path, string_template)

        self.regrid_method = ''
        self.regrid_tool = ''
        self.table_realm = ''
        self.realm = ''
        self.setup_regrid_and_realm_vars()
        self.setup_out_file()
        self.setup_metrics_dictionary()

    def setup_metrics_dictionary(self):
        ''' Initalize the results dict (metrics_dictionary) and the metrics documentation
        dict (metrics_def_dictionary) which is put in the results dict. '''
        self.metrics_def_dictionary = collections.OrderedDict()
        self.metrics_dictionary = collections.OrderedDict()
        self.metrics_dictionary["DISCLAIMER"] = self.open_disclaimer()
        self.metrics_dictionary["RESULTS"] = collections.OrderedDict()

        self.metrics_dictionary["Variable"] = {}
        self.metrics_dictionary["Variable"]["id"] = self.var
        self.metrics_dictionary["json_version"] = '3.0'
        self.metrics_dictionary["References"] = {}
        self.metrics_dictionary["RegionalMasking"] = {}

        level = DataSet.calculate_level_from_var(self.var_name_long)
        if level is None:
            self.out_file.level = ''
        else:
            self.metrics_dictionary["Variable"]["level"] = level
            self.out_file.level = "-%i" % (int(level / 100.0))

    def open_disclaimer(self):
        ''' Return the contents of disclaimer.txt. '''
        f = DataSet.load_path_as_file_obj('disclaimer.txt')
        contents = f.read()
        f.close()
        return contents

    def setup_regrid_and_realm_vars(self):
        ''' Set the regrid_method, regrid_tool, table_realm,
        and realm based off the obs dict and var. '''
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
        ''' Setup for the out_file, which outputs both the .json and .txt. '''
        self.out_file.set_target_grid(
            self.parameter.target_grid, self.regrid_tool, self.regrid_method)
        self.out_file.variable = self.var
        self.out_file.realm = self.realm
        self.out_file.table = self.table_realm
        self.out_file.case_id = self.parameter.case_id
        DataSet.apply_custom_keys(self.out_file, self.parameter.custom_keys, self.var)

    def add_region(self, region):
        ''' Add a region to the metrics_dictionary. '''
        self.metrics_dictionary['RegionalMasking'][self.get_region_name_from_region(region)] = region

    def calculate_and_output_metrics(self, ref, test):
        ''' Given ref and test (both either of type Observation or Model), compute the metrics. '''
        if isinstance(self.obs_dict[self.var][ref.obs_or_model], (str, unicode)):
            self.obs_var_ref = self.obs_dict[self.var][self.obs_dict[self.var][ref.obs_or_model]]
        else:
            self.obs_var_ref = self.obs_dict[self.var][ref.obs_or_model]

        self.metrics_dictionary['References'][ref.obs_or_model] = self.obs_var_ref

        try:
            ref_data = ref()
        except Exception as e:
            msg = 'Error while processing observation %s for variables %s:\n\t%s'
            logging.getLogger("pcmdi_metrics").error(msg % (self.var, str(e)))

        try:
            test_data = test()
        except RuntimeError as e:
            # THIS EXCEPTION IS RAISED TO BREAK OUT OF THE FOR LOOP IN PCMDI_DRIVER
            # THIS SHOULD BE A CUSTOM EXCEPTION (PrematureBreakError)
            raise RuntimeError('Need to skip model: %s' % test.obs_or_model)

        # Todo: Make this a fcn
        self.set_grid_in_metrics_dictionary(test_data)

        if ref_data.shape != test_data.shape:
            raise RuntimeError('Two data sets have different shapes. %s vs %s' % (ref_data.shape, test_data.shape))

        self.set_simulation_desc(test, test_data)

        if ref.obs_or_model not in self.metrics_dictionary['RESULTS'][test.obs_or_model]:
            self.metrics_dictionary["RESULTS"][test.obs_or_model][ref.obs_or_model] = \
                {'source': self.obs_dict[self.var][ref.obs_or_model]}

        parameter_realization = self.metrics_dictionary["RESULTS"][test.obs_or_model][ref.obs_or_model].\
            get(self.parameter.realization, {})

        if not self.parameter.dry_run:
            pr_rgn = pcmdi_metrics.pcmdi.compute_metrics(self.var_name_long, test_data, ref_data)

            # Calling compute_metrics with None for the model and obs returns
            # the definitions.
            self.metrics_def_dictionary.update(
                pcmdi_metrics.pcmdi.compute_metrics(self.var_name_long, None, None))
            if hasattr(self.parameter, 'compute_custom_metrics'):
                pr_rgn.update(
                    self.parameter.compute_custom_metrics(self.var_name_long,
                                                          test_data, ref_data))
                try:
                    self.metrics_def_dictionary.update(
                        self.parameter.compute_custom_metrics(
                            self.var_name_long, None, None))
                except:
                    self.metrics_def_dictionary.update(
                        {'custom': self.parameter.compute_custom_metrics.__doc__})

            parameter_realization[self.get_region_name_from_region(ref.region)] = collections.OrderedDict(
                (k, pr_rgn[k]) for k in sorted(pr_rgn.keys())
            )

            self.metrics_dictionary['RESULTS'][test.obs_or_model][ref.obs_or_model][self.parameter.realization] = \
                parameter_realization

        if self.check_save_test_clim(ref):
            self.output_interpolated_model_climatologies(test, test_data)

        self.write_on_exit()

    def set_grid_in_metrics_dictionary(self, test_data):
        ''' Set the grid in metrics_dictionary. '''
        grid = {}
        grid['RegridMethod'] = self.regrid_method
        grid['RegridTool'] = self.regrid_tool
        grid['GridName'] = self.parameter.target_grid
        grid['GridResolution'] = test_data.shape[1:]
        self.metrics_dictionary['GridInfo'] = grid

    def set_simulation_desc(self, test, test_data):
        ''' Fillout information for the output .json and .txt files. '''
        self.metrics_dictionary["RESULTS"][test.obs_or_model] = \
            self.metrics_dictionary["RESULTS"].get(test.obs_or_model, {})
        if "SimulationDescription" not in \
                self.metrics_dictionary["RESULTS"][test.obs_or_model]:

            descr = {"MIPTable": self.obs_var_ref["CMIP_CMOR_TABLE"],
                     "Model": test.obs_or_model,
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
                getattr(self.parameter, "simulation_description_mapping", {}))

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
                        f = cdms2.open(test.file_path())
                        if hasattr(f, a):
                            try:
                                vals.append(float(getattr(f, a)))
                            except:
                                vals.append(getattr(f, a))
                        # Ok couldn't find it anywhere
                        # setting to N/A
                        else:
                            vals.append("N/A")
                        f.close()
                descr[att] = fmt % tuple(vals)

            self.metrics_dictionary["RESULTS"][test.obs_or_model]["units"] = \
                getattr(test_data, "units", "N/A")
            self.metrics_dictionary["RESULTS"][test.obs_or_model]["SimulationDescription"] = descr

            self.metrics_dictionary["RESULTS"][test.obs_or_model]["InputClimatologyFileName"] = \
                os.path.basename(test.file_path())
            self.metrics_dictionary["RESULTS"][test.obs_or_model]["InputClimatologyMD5"] = test.hash()
            # Not just global
            # TODO Ask Charles if the below check is needed
            # if len(self.regions_dict[self.var]) > 1:
            self.metrics_dictionary["RESULTS"][test.obs_or_model][
                "InputRegionFileName"] = \
                self.sftlf[test.obs_or_model]["filename"]
            self.metrics_dictionary["RESULTS"][test.obs_or_model][
                "InputRegionMD5"] = \
                self.sftlf[test.obs_or_model]["md5"]

    def output_interpolated_model_climatologies(self, test, test_data):
        ''' Save the netCDF file. '''
        region_name = self.get_region_name_from_region(test.region)
        pth = os.path.join(self.parameter.test_clims_interpolated_output,
                           region_name)
        clim_file = Base(pth, self.parameter.filename_output_template)
        logging.getLogger("pcmdi_metrics").info('Saving interpolated climatologies to: %s' % clim_file())
        clim_file.level = self.out_file.level
        clim_file.model_version = test.obs_or_model

        clim_file.table = self.table_realm
        clim_file.period = self.parameter.period
        clim_file.case_id = self.parameter.case_id
        clim_file.set_target_grid(
            self.parameter.target_grid,
            self.regrid_tool,
            self.regrid_method)
        clim_file.variable = self.var
        clim_file.region = region_name
        clim_file.realization = self.parameter.realization
        DataSet.apply_custom_keys(clim_file, self.parameter.custom_keys, self.var)
        clim_file.write(test_data, type="nc", id=self.var)

    def get_region_name_from_region(self, region):
        ''' Extract the region name from the region dict. '''
        # region is both in ref and test
        region_name = region['id']
        if region is None:
            region_name = 'global'
        return region_name

    def check_save_test_clim(self, ref):
        ''' Bunch of checks to see if the netCDF files are needed to be saved. '''
        # Since we are only saving once per reference data set (it's always
        # the same after), we need to check if ref is the first value from the
        # parameter, hence we have ref.obs_or_model == reference_data_set[0]
        reference_data_set = self.parameter.reference_data_set
        reference_data_set = Observation.setup_obs_list_from_parameter(
            reference_data_set, self.obs_dict, self.var)
        return not self.parameter.dry_run and hasattr(self.parameter, 'save_test_clims') \
               and self.parameter.save_test_clims is True and ref.obs_or_model == reference_data_set[0]  # noqa

    def write_on_exit(self):
        ''' Output the metrics_dictionary as a json and text file. '''
        self.metrics_dictionary['METRICS'] = self.metrics_def_dictionary
        if not self.parameter.dry_run:
            logging.getLogger("pcmdi_metrics").info('Saving results to: %s' % self.out_file())
            self.out_file.write(self.metrics_dictionary,
                                json_structure=["model", "reference", "rip", "region", "statistic", "season"],
                                indent=4,
                                separators=(',', ': '))
            self.out_file.write(self.metrics_dictionary, type='txt')
