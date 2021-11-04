import MV2
import cdutil


def compute(dm, do):
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

    # mae = MV.average(MV.absolute(MV.subtract(dm, do))) - depricated ... did
    # not include area weights
    return float(mae)
