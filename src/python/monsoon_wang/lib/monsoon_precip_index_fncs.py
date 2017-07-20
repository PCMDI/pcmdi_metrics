import numpy
import MV2

#  SEASONAL RANGE - USING ANNUAL CYCLE CLIMATOLGIES 0=Jan, 11=Dec

def compute_season(data,season_indices,weights):
    out = numpy.ma.zeros(data.shape[1:],dtype=data.dtype)
    N=0
    for i in season_indices:
        out+=data[i]*weights[i]
        N+=weights[i]
    out = MV2.array(out)
    out.id = data.id
    out.setAxisList(data.getAxisList()[1:])
    return out/N

def mpd(data):
    """Monsoon precipitation intensity and annual range calculation

           .. describe:: Input

               *  data

                   * Assumes climatology array with 12 times step first one January

   """
    months_length = [31., 28., 31., 30., 31., 30., 31., 31., 30., 31., 30., 31.]
    mjjas = compute_season(data,[4,5,6,7,8],months_length)
    ndjfm = compute_season(data,[10, 11, 0, 1, 2],months_length)
    ann = compute_season(data,range(12),months_length)


    annrange = MV2.subtract(mjjas, ndjfm)

    lat = annrange.getAxis(0)
    i, e = lat.mapInterval((-91, 0, 'con'))
    if i > e:  # reveresedlats
        tmp = i + 1
        i = e + 1
        e = tmp

    annrange[slice(i, e)] = -annrange[slice(i, e)]
    annrange.id = data.id+"_ar"
    annrange.longname = "annual range"

    mpi = MV2.divide(annrange, ann)
    mpi.id = data.id+"_int"
    mpi.longname = "intensity"

    return annrange, mpi


def mpi_skill_scores(annrange_mod_dom, annrange_obs_dom, threshold=2.5 / 86400.):
    """Monsoon precipitation index skill score calculation
       see Wang et al., doi:10.1007/s00382-010-0877-0

         .. describe:: Input

             *  annrange_mod_dom

                 * Model Values Range (summer - winter)

             *  annrange_obs_dom

                 * Observations Values Range (summer - winter)

             *  threshold [default is 2.5/86400.]

                 * threshold in same units as inputs
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

    score = hit / (hit + missed + falarm)

    hitmap.id = 'hit'
    missmap.id = 'miss'
    falarmmap.id = 'false_alarm'

    for a in [hitmap,missmap,falarmmap]:
        a.setAxisList(annrange_mod_dom.getAxisList())

    return hit, missed, falarm, score, hitmap, missmap, falarmmap
