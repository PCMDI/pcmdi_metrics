import numpy
import MV2

#  SEASONAL RANGE - USING ANNUAL CYCLE CLIMATOLGIES 0=Jan, 11=Dec


def mpd(data):
    """Monsoon precipitation index calculation

           .. describe:: Input

               *  data

                   * Assumes climatology array with 12 times step first one January

   """
    mjjas = MV2.average(data[4:9])
    ndjfm = (data[10] + data[11] + data[0] + data[1] + data[2]) / 5.
    ann = MV2.average(data, axis=0)

    annrange = MV2.subtract(mjjas, ndjfm)

    lat = annrange.getAxis(0)
    i, e = lat.mapInterval((-91, 0, 'con'))
    if i > e:  # reveresedlats
        tmp = i + 1
        i = e + 1
        e = tmp

    annrange[slice(i, e)] = -annrange[slice(i, e)]
    annrange.id = 'annrange'

    mpi = MV2.divide(annrange, ann)

    return annrange, mpi


def mpi_skill_scores(annrange_mod_dom, annrange_obs_dom, threshold=1. / 43200.):
    """Monsoon precipitation index skill score calculation

         .. describe:: Input

             *  annrange_mod_dom

                 * blah

             *  annrange_bos_dom

                 * blah

             *  threshold [default is 2./86400.]

                 * threshol is set converted from mm/day to kgs-1m-2
 """
    mt = numpy.ma.greater(annrange_mod_dom, threshold)
    ot = numpy.ma.greater(annrange_obs_dom, threshold)

    hitmap = mt * ot  # only where both  mt and ot are True
    hit = float(hitmap.sum())

    xor = numpy.ma.logical_xor(mt, ot)
    missmap = xor * ot
    missed = float(MV2.sum(missmap))

    falarmmap = xor * mt
    falarm = float(MV2.sum(falarmmap))

#  print mod,' hit missed falarm ', hit,' ', missed,' ', falarm

    score = hit / (hit + missed + falarm)
    hitmap.id = 'hit'
    missmap.id = 'miss'
    falarmmap.id = 'false_alarm'
    # for a in [hitmap,missmap,falarmmap]:
    #    a.setAxisList(annrange_mod_dom.getAxisList())
    return hit, missed, falarm, score, hitmap, missmap, falarmmap
