""" Calculate metrics based on Sperber and Annamalai 2014 Clim. Dyn.,
which are:
- onset pentad index: when fractional accumulation hit 20%
- decay pentad index: when fractional accumulation hit 80%
- slope: slope between onset and decay pentad time step indices
calculated from cumulative pentad time series

Jiwoo Lee, 2018-07

Note: Code for picking onset/decay index inspired by
https://stackoverflow.com/questions/2236906/first-python-list-index-greater-than-x
"""

import MV2


def sperber_metrics(d, region, debug=False):
    """ d: input, 1d array of cumulative pentad time series """
    # Convert accumulation to fractional accumulation; normalize by sum
    d_sum = d[-1]
    frac_accum = MV2.divide(d, d_sum)
    onset_index = next(i for i, v in enumerate(frac_accum) if v >= 0.2)
    if region == 'GoG':
        decay_threshold = 0.6
    else:
        decay_threshold = 0.8
    decay_index = next(i for i, v in enumerate(
        frac_accum) if v >= decay_threshold)
    slope = (frac_accum[decay_index] - frac_accum[onset_index]) \
        / float(decay_index - onset_index)
    duration = decay_index - onset_index + 1
    return {'frac_accum': frac_accum,
            'onset_index': onset_index,
            'decay_index': decay_index,
            'slope': slope}
            'duration': duration}
