import cdutil,cdms2

def compute(d,sea):
    """ Computes SEASONAL MEAN"""

    djf_ind = [11,0,1]
    mam_ind = [2,3,4]
    jja_ind = [5,6,7]
    son_ind = [8,9,10]
    mo_wts = [31,31,28.25,31,30,31,30,31,31,30,31,30]

    if sea == 'djf': indx = [11,0,1]
    if sea == 'mam': indx = [2,3,4]
    if sea == 'jja': indx = [5,6,7]
    if sea == 'son': indx = [8,9,10]

    sea_no_days = mo_wts[indx[0]] + mo_wts[indx[1]] + mo_wts[indx[2]]

    d_sea = (d[indx[0]]*mo_wts[indx[0]] + d[indx[1]]*mo_wts[indx[1]] + d[indx[2]]*mo_wts[indx[2]])/sea_no_days

    return d_sea 
