import MV2
import cdutil


def compute(dm, do):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dif = MV2.subtract(dm, do)
    return MV2.float(cdutil.averager(dif, axis="xyt", weights="weighted"))


# return MV2.float(MV2.average(MV2.subtract(dm, do))) deprecated - does
# not use area weights
