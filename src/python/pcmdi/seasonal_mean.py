def compute(d, sea):
    """ Computes SEASONAL MEAN"""
    if d is None and sea is None:  # just want the doc
        return {
            "Name": "Seasonal Mean",
            "Abstract": "Compute Seasonal Mean",
            "Contact": "Peter Gleckler <gleckler1@llnl.gov>",
            "Comments": "Assumes input are 12 months climatology"
        }

    mo_wts = [31, 31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30]

    if sea == 'djf':
        indx = [11, 0, 1]
    if sea == 'mam':
        indx = [2, 3, 4]
    if sea == 'jja':
        indx = [5, 6, 7]
    if sea == 'son':
        indx = [8, 9, 10]

    sea_no_days = mo_wts[indx[0]] + mo_wts[indx[1]] + mo_wts[indx[2]]

    d_sea = (d[indx[0]] * mo_wts[indx[0]] + d[indx[1]] * mo_wts[indx[1]] + d[indx[2]] * mo_wts[indx[2]]) / sea_no_days

    return d_sea
