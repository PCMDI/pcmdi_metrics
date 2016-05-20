import cdms2 as cdms
import pcmdi_metrics
import collections
import MV2 as MV
from genutil import grower


def compute_metrics(Var, dm_glb, do_glb):
    # Var is sometimes sent with level associated
    var = Var.split("_")[0]
    # Did we send data? Or do we just want the info?
    if dm_glb is None and do_glb is None:
        metrics_defs = collections.OrderedDict()
        metrics_defs["rms_xyt"] = pcmdi_metrics.pcmdi.rms_xyt.compute(
            None,
            None)
        metrics_defs["rms_xy"] = pcmdi_metrics.pcmdi.rms_xy.compute(None, None)
        metrics_defs["bias_xy"] = pcmdi_metrics.pcmdi.bias.compute(None, None)
        metrics_defs["mae_xy"] = pcmdi_metrics.pcmdi.meanabs_xy.compute(
            None,
            None)
        metrics_defs["cor_xyt"] = pcmdi_metrics.pcmdi.cor_xyt.compute(
            None,
            None)
        metrics_defs["cor_xy"] = pcmdi_metrics.pcmdi.cor_xy.compute(None, None)

        metrics_defs["std_xy"] = pcmdi_metrics.pcmdi.std_xy.compute(None)
        metrics_defs["std_xyt"] = pcmdi_metrics.pcmdi.std_xyt.compute(None)

        metrics_defs["seasonal_mean"] = \
            pcmdi_metrics.pcmdi.seasonal_mean.compute(
            None,
            None)
        metrics_defs["annual_mean"] = pcmdi_metrics.pcmdi.annual_mean.compute(
            None,
            None)
        metrics_defs["zonal_mean"] = pcmdi_metrics.pcmdi.zonal_mean.compute(
            None,
            None)
        return metrics_defs
    cdms.setAutoBounds('on')
    metrics_dictionary = {}

    # SET CONDITIONAL ON INPUT VARIABLE
    if var == 'pr':
        conv = 1.e5
    else:
        conv = 1.

    if var in ['hus']:
        sig_digits = '.5f'
    else:
        sig_digits = '.3f'

    domains = ['GLB', 'NHEX', 'TROPICS', 'SHEX']

    for dom in domains:

        dm = dm_glb
        do = do_glb

        if dom == 'NHEX':
            dm = dm_glb(latitude=(30., 90))
            do = do_glb(latitude=(30., 90))
        if dom == 'SHEX':
            dm = dm_glb(latitude=(-90., -30))
            do = do_glb(latitude=(-90., -30))
        if dom == 'TROPICS':
            dm = dm_glb(latitude=(-30., 30))
            do = do_glb(latitude=(-30., 30))

        # CALCULATE ANNUAL CYCLE SPACE-TIME RMS, CORRELATIONS and STD
        rms_xyt = pcmdi_metrics.pcmdi.rms_xyt.compute(dm, do)
        cor_xyt = pcmdi_metrics.pcmdi.cor_xyt.compute(dm, do)
        stdObs_xyt = pcmdi_metrics.pcmdi.std_xyt.compute(do)
        std_xyt = pcmdi_metrics.pcmdi.std_xyt.compute(dm)

        # CALCULATE ANNUAL MEANS
        dm_am, do_am = pcmdi_metrics.pcmdi.annual_mean.compute(dm, do)

        # CALCULATE ANNUAL MEAN BIAS
        bias_xy = pcmdi_metrics.pcmdi.bias.compute(dm_am, do_am)

        # CALCULATE MEAN ABSOLUTE ERROR
        mae_xy = pcmdi_metrics.pcmdi.meanabs_xy.compute(dm_am, do_am)

        # CALCULATE ANNUAL MEAN RMS
        rms_xy = pcmdi_metrics.pcmdi.rms_xy.compute(dm_am, do_am)

        # CALCULATE ANNUAL OBS STD 
        stdObs_xy = pcmdi_metrics.pcmdi.std_xy.compute(do_am)
        std_xy = pcmdi_metrics.pcmdi.std_xy.compute(dm_am)

        # ZONAL MEANS ######
        # CALCULATE ANNUAL MEANS
        dm_amzm, do_amzm = pcmdi_metrics.pcmdi.zonal_mean.compute(dm_am, do_am)

        # CALCULATE ANNUAL AND ZONAL MEAN RMS
        rms_y = pcmdi_metrics.pcmdi.rms_0.compute(dm_amzm, do_amzm)

        # CALCULATE ANNUAL MEAN DEVIATION FROM ZONAL MEAN RMS
        dm_amzm_grown, dummy = grower(dm_amzm, dm_am)
        dm_am_devzm = MV.subtract(dm_am, dm_amzm_grown)
        do_amzm_grown, dummy = grower(do_amzm, do_am)
        do_am_devzm = MV.subtract(do_am, do_amzm_grown)
        rms_xy_devzm = pcmdi_metrics.pcmdi.rms_xy.compute(
            dm_am_devzm, do_am_devzm)

        # CALCULATE ANNUAL AND ZONAL MEAN STD 

        # CALCULATE ANNUAL MEAN DEVIATION FROM ZONAL MEAN STD  
        stdObs_xy_devzm = pcmdi_metrics.pcmdi.std_xy.compute(do_am_devzm)
        std_xy_devzm = pcmdi_metrics.pcmdi.std_xy.compute(dm_am_devzm)

        metrics_dictionary[
            'std-obs_xy_ann_' +
            dom] = format(
            stdObs_xy *
            conv,
            sig_digits)
        metrics_dictionary[
            'std_xy_ann_' +
            dom] = format(
            std_xy *
            conv,
            sig_digits)
        metrics_dictionary[
            'std-obs_xyt_ann_' +
            dom] = format(
            stdObs_xyt *
            conv,
            sig_digits)
        metrics_dictionary[
            'std_xyt_ann_' +
            dom] = format(
            std_xyt *
            conv,
            sig_digits)
        metrics_dictionary[
            'std-obs_xy_devzm_ann_' +
            dom] = format(
            stdObs_xy_devzm *
            conv,
            sig_digits)
        metrics_dictionary[
            'std_xy_devzm_ann_' +
            dom] = format(
            std_xy_devzm *
            conv,
            sig_digits)
        metrics_dictionary[
            'rms_xyt_ann_' +
            dom] = format(
            rms_xyt *
            conv,
            sig_digits)
        metrics_dictionary[
            'rms_xy_ann_' +
            dom] = format(
            rms_xy *
            conv,
            sig_digits)
        metrics_dictionary[
            'bias_xy_ann_' +
            dom] = format(
            bias_xy *
            conv,
            sig_digits)
        metrics_dictionary[
            'cor_xyt_ann_' +
            dom] = format(
            cor_xyt *
            conv,
            '.2f')
        metrics_dictionary[
            'mae_xy_ann_' +
            dom] = format(
            mae_xy *
            conv,
            sig_digits)
# ZONAL MEAN CONTRIBUTIONS
        metrics_dictionary[
            'rms_y_ann_' +
            dom] = format(
            rms_y *
            conv,
            sig_digits)
        metrics_dictionary[
            'rms_devzm_ann_' +
            dom] = format(
            rms_xy_devzm *
            conv,
            sig_digits)

        # CALCULATE SEASONAL MEANS
        for sea in ['djf', 'mam', 'jja', 'son']:

            dm_sea = pcmdi_metrics.pcmdi.seasonal_mean.compute(dm, sea)
            do_sea = pcmdi_metrics.pcmdi.seasonal_mean.compute(do, sea)

            # CALCULATE SEASONAL RMS AND CORRELATION
            rms_sea = pcmdi_metrics.pcmdi.rms_xy.compute(dm_sea, do_sea)
            cor_sea = pcmdi_metrics.pcmdi.cor_xy.compute(dm_sea, do_sea)
            mae_sea = pcmdi_metrics.pcmdi.meanabs_xy.compute(dm_sea, do_sea)
            bias_sea = pcmdi_metrics.pcmdi.bias.compute(dm_sea, do_sea)

        # ZONAL MEANS ######
        # CALCULATE SEASONAL MEANS
# dm_smzm, do_smzm = pcmdi_metrics.pcmdi.zonal_mean.compute(dm_sea,
# do_sea)

        # CALCULATE SEASONAL AND ZONAL MEAN RMS
#           rms_y = pcmdi_metrics.pcmdi.rms_y.compute(dm_smzm, do_smzm)

        # CALCULATE SEASONAL MEAN DEVIATION FROM ZONAL MEAN RMS
#           dm_smzm_grown,dummy = grower(dm_smzm,dm_sea)
#           dm_sea_devzm = MV.subtract(dm_sea,dm_smzm_grown)
#           do_smzm_grown,dummy = grower(do_smzm,do_sea)
#           do_sm_devzm = MV.subtract(do_sea,do_smzm_grown)
# rms_xy_devzm = pcmdi_metrics.pcmdi.rms_xy.compute(dm_sm_devzm,
# do_sm_devzm)

#           print 'SEASONAL ZM HERE>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'

            metrics_dictionary[
                'bias_xy_' +
                sea +
                '_' +
                dom] = format(
                bias_sea *
                conv,
                sig_digits)
            metrics_dictionary[
                'rms_xy_' +
                sea +
                '_' +
                dom] = format(
                rms_sea *
                conv,
                sig_digits)
            metrics_dictionary[
                'cor_xy_' +
                sea +
                '_' +
                dom] = format(
                cor_sea,
                '.2f')
            metrics_dictionary[
                'mae_xy_' +
                sea +
                '_' +
                dom] = format(
                mae_sea *
                conv,
                sig_digits)

# ZONAL AND SEASONAL MEAN CONTRIBUTIONS
#           metrics_dictionary[
#              'rms_y_' + sea + '_' +
#              dom] = format(
#              rms_y *
#              conv,
#              sig_digits)
#           metrics_dictionary[
#              'rms_devzm_' + sea + '_' +
#              dom] = format(
#              rms_xy_devzm *
#              conv,
#              sig_digits)

    return metrics_dictionary
