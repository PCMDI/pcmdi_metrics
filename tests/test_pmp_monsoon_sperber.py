from __future__ import print_function

import cdms2
import cdutil
import json
import MV2
import numpy as np
import os
import pcmdi_metrics
import basepmp
from collections import defaultdict
from pcmdi_metrics.monsoon_sperber import model_land_only, divide_chunks_advanced, sperber_metrics
import cdat_info


class PMPMonsoonSperberTest(basepmp.PMPTest):
    def testSperber(self):
        # GPCP 1 year
        inputfile = os.path.join(cdat_info.get_sampledata_path(),
                                 'test_monsoon_sperber_input.nc')
        model = 'obs'
        reference_data_name = 'GPCP'
        var = 'pr'
        # Landsea mask rewitten from NCL's 1x1
        inputfile_lf = os.path.join(cdat_info.get_sampledata_path(),
                                    'test_monsoon_sperber_input_lf.nc')
        region = 'AIR'
        n = 5
        debug = False

        # Read daily data
        f = cdms2.open(inputfile)
        d = f(var)

        # Read land fraction
        f_lf = cdms2.open(inputfile_lf)
        lf = f_lf('sftlf')

        # unit change
        d = MV2.multiply(d, 86400.)
        d.units = 'mm/d'

        # land only
        d_land = model_land_only(model, d, lf, debug=debug)

        # extract for monsoon region
        d_sub = d_land

        # area average
        d_sub_aave = cdutil.averager(d_sub, axis='xy', weights='weighted')

        # get pentad time series
        list_d_sub_aave_chunks = list(divide_chunks_advanced(d_sub_aave, n, debug=debug))
        pentad_time_series = []
        for d_sub_aave_chunk in list_d_sub_aave_chunks:
            if d_sub_aave_chunk.shape[0] >= n:  # ignore when chunk length is shorter than defined
                ave_chunk = MV2.average(d_sub_aave_chunk, axis=0)
                pentad_time_series.append(float(ave_chunk))

        pentad_time_series = MV2.array(pentad_time_series)
        pentad_time_series.units = d.units
        pentad_time_series_cumsum = np.cumsum(pentad_time_series)

        # Metrics
        metrics_result = sperber_metrics(pentad_time_series_cumsum, region, debug=debug)

        # Dict
        def tree():
            return defaultdict(tree)

        monsoon_stat_dic = tree()
        monsoon_stat_dic["RESULTS"]['REF'][reference_data_name][region]['onset_index'] = metrics_result['onset_index']
        monsoon_stat_dic["RESULTS"]['REF'][reference_data_name][region]['decay_index'] = metrics_result['decay_index']
        monsoon_stat_dic["RESULTS"]['REF'][reference_data_name][region]['slope'] = metrics_result['slope']

        # Archive in JSOS
        JSON = pcmdi_metrics.io.base.Base('.', 'test_monsoon_sperber.json')
        JSON.write(monsoon_stat_dic,
                json_structure=["model",
                                "realization",
                                "monsoon_region",
                                "metric"],
                sort_keys=True,
                indent=4,
                separators=(',', ': '))
        self.assertSimilarJsons('test_monsoon_sperber.json', 'tests/sperber_monsoon/test_monsoon_sperber.json')
