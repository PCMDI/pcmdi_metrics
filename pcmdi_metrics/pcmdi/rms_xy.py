import genutil


def compute(dm, do):
    """ Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Spatial Root Mean Square",
            "URI": "http://uvcdat.llnl.gov/documentation/" +
            "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.rms(dm, do, axis='xy', weights='weighted'))
