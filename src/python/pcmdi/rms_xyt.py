import genutil


def compute(dm, do):
    """ Computes rms """
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatio-Temporal Root Mean Square",
            "Abstract": "Compute Spatial and Temporal Root Mean Square",
            "URI": "http://uvcdat.llnl.gov/documentation/" +
            "utilities/utilities-2.html",
            "Contact": "Peter Gleckler <gleckler1@llnl.gov>",
        }
    return float(
        genutil.statistics.rms(dm, do, axis='xyt', weights='weighted'))
