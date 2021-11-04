import cdutil
import cdms2


def compute(dm, do):
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
