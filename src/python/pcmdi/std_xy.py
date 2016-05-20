import genutil


def compute(d):
    """ Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial Standard Deviation",
            "Abstract": "Compute Spatial Standard Deviation",
            "URI": "http://uvcdat.llnl.gov/documentation/" +
            "utilities/utilities-2.html",
            "Contact": "Peter Gleckler <gleckler1@llnl.gov>",
        }
    return float(genutil.statistics.std(d, axis='xy', weights='weighted'))


