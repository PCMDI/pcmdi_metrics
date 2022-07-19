import cdutil


def compute(dm, do):
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
