import genutil


def compute(dm, do):
    """ Computes correlation"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Correlation",
            "Abstract": "Compute Spatial Correlation",
            "URI": "http://uvcdat.llnl.gov/documentation/utilities/" +
            "utilities-2.html",
            "Contact": "Peter Gleckler <gleckler1@llnl.gov>",
        }
    return float(genutil.statistics.correlation(
        dm, do, axis='xy', weights='weighted'))
