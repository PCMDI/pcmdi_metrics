import cdms2
import cdutil
import genutil
import MV2


def annual_mean(dm, do):
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
    # Do we really want this? Wouldn't it better to let it fails
    cdms2.setAutoBounds("on")
    return cdutil.averager(dm, axis="t"), cdutil.averager(do, axis="t")


def bias_xy(dm, do):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dif = MV2.subtract(dm, do)
    return MV2.float(cdutil.averager(dif, axis="xy", weights="weighted"))


def bias_xyt(dm, do):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dif = MV2.subtract(dm, do)
    return MV2.float(cdutil.averager(dif, axis="xyt", weights="weighted"))


def cor_xy(dm, do):
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


def cor_xyt(dm, do):
    """Computes correlation"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial and Temporal Correlation",
            "Abstract": "Compute Spatio-Temporal Correlation",
            "URI": "http://uvcdat.llnl.gov/documentation/utilities/"
            + "utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.correlation(dm, do, axis="xyt", weights="weighted"))


def mean_xy(d):
    """Computes bias"""
    if d is None:  # just want the doc
        return {
            "Name": "Mean",
            "Abstract": "Area Mean (area weighted)",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return MV2.float(cdutil.averager(d, axis="xy", weights="weighted"))


def meanabs_xy(dm, do):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    absdif = MV2.absolute(MV2.subtract(dm, do))
    mae = cdutil.averager(absdif, axis="xy", weights="weighted")
    return float(mae)


def meanabs_xyt(dm, do):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    absdif = MV2.absolute(MV2.subtract(dm, do))
    mae = cdutil.averager(absdif, axis="xyt", weights="weighted")
    return float(mae)


def rms_0(dm, do):
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


def rms_xy(dm, do):
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


def rms_xyt(dm, do):
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


def rmsc_xy(dm, do):
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


def seasonal_mean(d, sea):
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


def std_xy(d):
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


def std_xyt(d):
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


def zonal_mean(dm, do):
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