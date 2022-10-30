#import cdms2
import cdutil
import genutil
import MV2
import xcdat


def annual_mean(dm, do, var=None):
    """Computes ANNUAL MEAN"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Annual Mean",
            "Abstract": "Compute Annual Mean",
            "URI": "http://uvcdat.llnl.gov/documentation/"
            + "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
            "Comments": "Assumes input are 12 months climatology",
        }
    #cdms2.setAutoBounds("on")
    #return cdutil.averager(dm, axis="t"), cdutil.averager(do, axis="t")
    dm_am = dm.temporal.average(var)
    do_am = do.temporal.average(var)
    


def bias_xy(dm, do, var=None):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['dif'] = dm[var] - do[var]
    stat = dm.spatial.average('dif', axis=['X', 'Y'])['dif'].values
    return float(stat)


def bias_xyt(dm, do, var=None):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dif = MV2.subtract(dm, do)
    dm['dif'] = dm[var] - do[var]
    stat = dm.spatial.average('dif', axis=['X', 'Y']).temporal.average('absdif')['absdif'].values
    return float(stat)


def cor_xy(dm, do, var=None):
    """Computes correlation"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Correlation",
            "Abstract": "Compute Spatial Correlation",
            "URI": "http://uvcdat.llnl.gov/documentation/utilities/"
            + "utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.correlation(dm, do, axis="xy", weights="weighted"))


def mean_xy(d, var=None):
    """Computes bias"""
    if d is None:  # just want the doc
        return {
            "Name": "Mean",
            "Abstract": "Area Mean (area weighted)",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    mean_xy = d.spatial.average(var, axis=['X', 'Y']).values
    return float(mean_xy)


def meanabs_xy(dm, do, var=None):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['absdif'] = abs(dm[var] - do[var])
    stat = dm.spatial.average('absdif', axis=['X', 'Y'])['absdif'].values
    return float(stat)


def meanabs_xyt(dm, do, var=None):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['absdif'] = abs(dm[var] - do[var])
    stat = dm.spatial.average('absdif', axis=['X', 'Y']).temporal.average('absdif')['absdif'].values
    return float(stat)


def rms_0(dm, do, var=None):
    """Computes rms over first axis"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Root Mean Square over First Axis",
            "Abstract": "Compute Root Mean Square over the first axis",
            "URI": "http://uvcdat.llnl.gov/documentation/"
            + "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if 1 in [x.isLevel() for x in dm.getAxisList()]:
        dm = dm(squeeze=1)
        do = do(squeeze=1)
    return float(genutil.statistics.rms(dm, do))


def rms_xy(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Spatial Root Mean Square",
            "URI": "http://uvcdat.llnl.gov/documentation/"
            + "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.rms(dm, do, axis="xy", weights="weighted"))


def rms_xyt(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatio-Temporal Root Mean Square",
            "Abstract": "Compute Spatial and Temporal Root Mean Square",
            "URI": "http://uvcdat.llnl.gov/documentation/"
            + "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.rms(dm, do, axis="xyt", weights="weighted"))


def rmsc_xy(dm, do, var=None):
    """Computes centered rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Centered Spatial Root Mean Square",
            "URI": "http://uvcdat.llnl.gov/documentation/"
            + "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(
        genutil.statistics.rms(dm, do, axis="xy", centered=1, weights="weighted")
    )


def seasonal_mean(d, sea, var=None):
    """Computes SEASONAL MEAN"""
    if d is None and sea is None:  # just want the doc
        return {
            "Name": "Seasonal Mean",
            "Abstract": "Compute Seasonal Mean",
            "Contact": "pcmdi-metrics@llnl.gov",
            "Comments": "Assumes input are 12 months climatology",
        }

    mo_wts = [31, 31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30]

    if sea == "djf":
        indx = [11, 0, 1]
    if sea == "mam":
        indx = [2, 3, 4]
    if sea == "jja":
        indx = [5, 6, 7]
    if sea == "son":
        indx = [8, 9, 10]

    sea_no_days = mo_wts[indx[0]] + mo_wts[indx[1]] + mo_wts[indx[2]]

    d_sea = (
        d[indx[0]] * mo_wts[indx[0]]
        + d[indx[1]] * mo_wts[indx[1]]
        + d[indx[2]] * mo_wts[indx[2]]
    ) / sea_no_days

    return d_sea


def std_xy(d, var=None):
    """Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial Standard Deviation",
            "Abstract": "Compute Spatial Standard Deviation",
            "URI": "http://uvcdat.llnl.gov/documentation/"
            + "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.std(d, axis="xy", weights="weighted"))


def std_xyt(d, var=None):
    """Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial-temporal Standard Deviation",
            "Abstract": "Compute Space-Time Standard Deviation",
            "URI": "http://uvcdat.llnl.gov/documentation/"
            + "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.std(d, axis="xyt", weights="weighted"))


def zonal_mean(dm, do, var=None):
    """Computes ZONAL MEAN assumes rectilinear/regular grid"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Zonal Mean",
            "Abstract": "Compute Zonal Mean",
            "URI": "http://uvcdat.llnl.gov/documentation/"
            + "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
            "Comments": "",
        }
    return cdutil.averager(dm, axis="x"), cdutil.averager(do, axis="x")
