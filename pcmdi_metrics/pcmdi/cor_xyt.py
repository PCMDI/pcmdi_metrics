import genutil


def compute(dm, do):
    """ Computes correlation"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial and Temporal Correlation",
            "Abstract": "Compute Spatio-Temporal Correlation",
            "URI": "http://uvcdat.llnl.gov/documentation/utilities/" +
            "utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.correlation(
        dm, do, axis='xyt', weights='weighted'))
