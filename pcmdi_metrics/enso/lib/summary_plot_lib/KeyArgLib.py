# -*- coding:UTF-8 -*-
from inspect import stack as INSPECTstack

# ENSO_metrics package functions:
from .EnsoErrorsWarnings import unknown_key_arg


# ---------------------------------------------------------------------------------------------------------------------#
#
# Library to ENSO metrics arguments (arg parser)
# These functions analyses given arguments and sets some arguments to their default value
#
def default_arg_values(arg):
    default = {
        'detrending': False, 'frequency': None, 'metric_computation': 'difference', 'min_time_steps': None,
        'normalization': False, 'project_interpreter': 'CMIP', 'regridding': False, 'smoothing': False,
        'treshold_ep_ev': -140, 'time_bounds': None, 'time_bounds_mod': None, 'time_bounds_obs': None,
    }
    try:
        default[arg]
    except:
        unknown_key_arg(arg, INSPECTstack())
    return default[arg]
# ---------------------------------------------------------------------------------------------------------------------#
