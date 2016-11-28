import cdms2 as cdms
import pcmdi_metrics
import collections
import MV2
from genutil import grower


def compute_metrics(Var, dm, do):
    # Var is sometimes sent with level associated
    var = Var.split("_")[0]
    # Did we send data? Or do we just want the info?
    if dm is None and do is None:
        metrics_defs = collections.OrderedDict()
        metrics_defs["rms_xyt"] = pcmdi_metrics.pcmdi.rms_xyt.compute(
            None,
            None)
        metrics_defs["rms_xy"] = pcmdi_metrics.pcmdi.rms_xy.compute(None, None)
        metrics_defs["rmsc_xy"] = pcmdi_metrics.pcmdi.rmsc_xy.compute(None, None)
        metrics_defs["bias_xy"] = pcmdi_metrics.pcmdi.bias_xy.compute(
            None, None)
        metrics_defs["mae_xy"] = pcmdi_metrics.pcmdi.meanabs_xy.compute(
            None,
            None)
        # metrics_defs["cor_xyt"] = pcmdi_metrics.pcmdi.cor_xyt.compute(
        #     None,
        #     None)
        metrics_defs["cor_xy"] = pcmdi_metrics.pcmdi.cor_xy.compute(None, None)
        metrics_defs["mean_xy"] = pcmdi_metrics.pcmdi.mean_xy.compute(None)
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
        conv = 86400.
    else:
        conv = 1.

    if var in ['hus']:
        sig_digits = '.5f'
    else:
        sig_digits = '.3f'

    # CALCULATE ANNUAL CYCLE SPACE-TIME RMS, CORRELATIONS and STD
    rms_xyt = pcmdi_metrics.pcmdi.rms_xyt.compute(dm, do)
#   cor_xyt = pcmdi_metrics.pcmdi.cor_xyt.compute(dm, do)
    stdObs_xyt = pcmdi_metrics.pcmdi.std_xyt.compute(do)
    std_xyt = pcmdi_metrics.pcmdi.std_xyt.compute(dm)

    # CALCULATE ANNUAL MEANS
    dm_am, do_am = pcmdi_metrics.pcmdi.annual_mean.compute(dm, do)

    # CALCULATE ANNUAL MEAN BIAS
    bias_xy = pcmdi_metrics.pcmdi.bias_xy.compute(dm_am, do_am)

    # CALCULATE MEAN ABSOLUTE ERROR
    mae_xy = pcmdi_metrics.pcmdi.meanabs_xy.compute(dm_am, do_am)

    # CALCULATE ANNUAL MEAN RMS (centered and uncentered)
    rms_xy = pcmdi_metrics.pcmdi.rms_xy.compute(dm_am, do_am)
    rmsc_xy = pcmdi_metrics.pcmdi.rmsc_xy.compute(dm_am, do_am)

    # CALCULATE ANNUAL MEAN CORRELATION
    cor_xy = pcmdi_metrics.pcmdi.cor_xy.compute(dm_am, do_am)

    # CALCULATE ANNUAL OBS and MOD STD
    stdObs_xy = pcmdi_metrics.pcmdi.std_xy.compute(do_am)
    std_xy = pcmdi_metrics.pcmdi.std_xy.compute(dm_am)

    # CALCULATE ANNUAL OBS and MOD MEAN
    meanObs_xy = pcmdi_metrics.pcmdi.mean_xy.compute(do_am)
    mean_xy = pcmdi_metrics.pcmdi.mean_xy.compute(dm_am)

    # ZONAL MEANS ######
    # CALCULATE ANNUAL MEANS
    dm_amzm, do_amzm = pcmdi_metrics.pcmdi.zonal_mean.compute(dm_am, do_am)

    # CALCULATE ANNUAL AND ZONAL MEAN RMS
    rms_y = pcmdi_metrics.pcmdi.rms_0.compute(dm_amzm, do_amzm)

    # CALCULATE ANNUAL MEAN DEVIATION FROM ZONAL MEAN RMS
    dm_amzm_grown, dummy = grower(dm_amzm, dm_am)
    dm_am_devzm = MV2.subtract(dm_am, dm_amzm_grown)
    do_amzm_grown, dummy = grower(do_amzm, do_am)
    do_am_devzm = MV2.subtract(do_am, do_amzm_grown)
    rms_xy_devzm = pcmdi_metrics.pcmdi.rms_xy.compute(
        dm_am_devzm, do_am_devzm)

    # CALCULATE ANNUAL AND ZONAL MEAN STD

    # CALCULATE ANNUAL MEAN DEVIATION FROM ZONAL MEAN STD
    stdObs_xy_devzm = pcmdi_metrics.pcmdi.std_xy.compute(do_am_devzm)
    std_xy_devzm = pcmdi_metrics.pcmdi.std_xy.compute(dm_am_devzm)

    for stat in ["std-obs_xy", "std_xy", "std-obs_xyt",
                 "std_xyt", "std-obs_xy_devzm", "mean_xy", "mean-obs_xy", "std_xy_devzm",
                 "rms_xyt", "rms_xy", "rmsc_xy", "cor_xy", "bias_xy",
                 "mae_xy", "rms_y", "rms_devzm"]:
        metrics_dictionary[stat] = {}

    metrics_dictionary[
        'mean-obs_xy']['ann'] = format(
        meanObs_xy *
        conv,
        sig_digits)
    metrics_dictionary[
        'mean_xy']['ann'] = format(
        mean_xy *
        conv,
        sig_digits)
    metrics_dictionary[
        'std-obs_xy']['ann'] = format(
        stdObs_xy *
        conv,
        sig_digits)
    metrics_dictionary[
        'std_xy']['ann'] = format(
        std_xy *
        conv,
        sig_digits)
    metrics_dictionary[
        'std-obs_xyt']['ann'] = format(
        stdObs_xyt *
        conv,
        sig_digits)
    metrics_dictionary[
        'std_xyt']['ann'] = format(
        std_xyt *
        conv,
        sig_digits)
    metrics_dictionary[
        'std-obs_xy_devzm']['ann'] = format(
        stdObs_xy_devzm *
        conv,
        sig_digits)
    metrics_dictionary[
        'std_xy_devzm']['ann'] = format(
        std_xy_devzm *
        conv,
        sig_digits)
    metrics_dictionary[
        'rms_xyt']['ann'] = format(
        rms_xyt *
        conv,
        sig_digits)
    metrics_dictionary[
        'rms_xy']['ann'] = format(
        rms_xy *
        conv,
        sig_digits)
    metrics_dictionary[
        'rmsc_xy']['ann'] = format(
        rmsc_xy *
        conv,
        sig_digits)
    metrics_dictionary[
        'cor_xy']['ann'] = format(
        cor_xy,
        sig_digits)
    metrics_dictionary[
        'bias_xy']['ann'] = format(
        bias_xy *
        conv,
        sig_digits)
    metrics_dictionary[
        'mae_xy']['ann'] = format(
        mae_xy *
        conv,
        sig_digits)
# ZONAL MEAN CONTRIBUTIONS
    metrics_dictionary[
        'rms_y']['ann'] = format(
        rms_y *
        conv,
        sig_digits)
    metrics_dictionary[
        'rms_devzm']['ann'] = format(
        rms_xy_devzm *
        conv,
        sig_digits)

    # CALCULATE SEASONAL MEANS
    for sea in ['djf', 'mam', 'jja', 'son']:

        dm_sea = pcmdi_metrics.pcmdi.seasonal_mean.compute(dm, sea)
        do_sea = pcmdi_metrics.pcmdi.seasonal_mean.compute(do, sea)

        # CALCULATE SEASONAL RMS AND CORRELATION
        rms_sea = pcmdi_metrics.pcmdi.rms_xy.compute(dm_sea, do_sea)
        rmsc_sea = pcmdi_metrics.pcmdi.rmsc_xy.compute(dm_sea, do_sea)
        cor_sea = pcmdi_metrics.pcmdi.cor_xy.compute(dm_sea, do_sea)
        mae_sea = pcmdi_metrics.pcmdi.meanabs_xy.compute(dm_sea, do_sea)
        bias_sea = pcmdi_metrics.pcmdi.bias_xy.compute(dm_sea, do_sea)

        # CALCULATE SEASONAL OBS and MOD STD
        stdObs_xy_sea = pcmdi_metrics.pcmdi.std_xy.compute(do_sea)
        std_xy_sea = pcmdi_metrics.pcmdi.std_xy.compute(dm_sea)

        # CALCULATE SEASONAL OBS and MOD MEAN
        meanObs_xy_sea = pcmdi_metrics.pcmdi.mean_xy.compute(do_sea)
        mean_xy_sea = pcmdi_metrics.pcmdi.mean_xy.compute(dm_sea)

        metrics_dictionary['bias_xy'][sea] = format(
            bias_sea *
            conv,
            sig_digits)
        metrics_dictionary['rms_xy'][sea] = format(
            rms_sea *
            conv,
            sig_digits)
        metrics_dictionary['rmsc_xy'][sea] = format(
            rmsc_sea *
            conv,
            sig_digits)
        metrics_dictionary['cor_xy'][sea] = format(
            cor_sea,
            '.2f')
        metrics_dictionary['mae_xy'][sea] = format(
            mae_sea *
            conv,
            sig_digits)
        metrics_dictionary['std-obs_xy'][sea] = format(
            stdObs_xy_sea *
            conv,
            sig_digits)
        metrics_dictionary['std_xy'][sea] = format(
            std_xy_sea *
            conv,
            sig_digits)
        metrics_dictionary['mean-obs_xy'][sea] = format(
            meanObs_xy_sea *
            conv,
            sig_digits)
        metrics_dictionary['mean_xy'][sea] = format(
            mean_xy_sea *
            conv,
            sig_digits)

# ZONAL AND SEASONAL MEAN CONTRIBUTIONS
#           metrics_dictionary[ 'rms_y'][ sea] = format(
#              rms_y *
#              conv,
#              sig_digits)
#           metrics_dictionary[ 'rms_devzm'][ sea] = format(
#              rms_xy_devzm *
#              conv,
#              sig_digits)

    return metrics_dictionary