import genutil


def compute(dm, do):
    """ Computes rms over first axis"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Root Mean Square over First Axis",
            "Abstract": "Compute Root Mean Square over the first axis",
            "URI": "http://uvcdat.llnl.gov/documentation/" +
            "utilities/utilities-2.html",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if 1 in [x.isLevel() for x in dm.getAxisList()]:
        print(dm.shape, "B4")
        dm = dm(squeeze=1)
        do = do(squeeze=1)
        print(dm.shape, "AF")
    return float(genutil.statistics.rms(dm, do))
