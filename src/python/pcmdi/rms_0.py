import genutil


def compute(dm, do):
    """ Computes rms over first axis"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Root Mean Square over First Axis",
            "Abstract": "Compute Root Mean Square over the first axis",
            "URI": "http://uvcdat.llnl.gov/documentation/" +
            "utilities/utilities-2.html",
            "Contact": "Peter Gleckler <gleckler1@llnl.gov>",
        }
    return float(genutil.statistics.rms(dm, do))
