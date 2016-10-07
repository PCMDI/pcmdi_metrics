import genutil


def compute(d):
    """ Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial-temporal Standard Deviation",
            "Abstract": "Compute Space-Time Standard Deviation",
            "URI": "http://uvcdat.llnl.gov/documentation/" +
            "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    return float(genutil.statistics.std(d, axis='xyt', weights='weighted'))
