import logging
from pcmdi_metrics.PMP.PMPParameter import *


class PMPDriverCheckParameter(object):

    @staticmethod
    def check_parameter(parameter):
        # Just check that the parameters use exist in the parameter object.
        # The validity for each option was already
        #  checked by the parameter itself.
        vars_to_check = ['case_id', 'model_versions', 'period', 'realization',
                         'vars', 'ref', 'target_grid', 'regrid_tool',
                         'regrid_method', 'regrid_tool_ocn',
                         'regrid_method_ocn', 'save_mod_clims',
                         'regions_specs', 'regions', 'custom_keys',
                         'filename_template',
                         'generate_surface_type_land_fraction',
                         'surface_type_land_fraction_filename_template',
                         'mod_data_path', 'obs_data_path',
                         'metrics_output_path',
                         'model_clims_interpolated_output',
                         'filename_output_template',
                         'custom_observations_path']

        for var in vars_to_check:
            if not hasattr(parameter, var):
                logging.error("%s is not in the parameter file!" % var)
                raise AttributeError("%s is not in the parameter file!" % var)
