import MV2
import cdutil


def compute(d):
    """Computes bias"""
    if d is None:  # just want the doc
        return {
            "Name": "Mean",
            "Abstract": "Area Mean (area weighted)",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return MV2.float(cdutil.averager(d, axis="xy", weights="weighted"))


# return MV2.float(MV2.average(MV2.subtract(dm, do))) deprecated - does
# not use area weights
