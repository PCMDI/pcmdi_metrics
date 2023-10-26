#!/usr/local/uvcdat/latest/bin/python

import glob
import os

import cdms2 as cdms
import MV2 as MV

cdms.setAutoBounds("on")

cdms.setNetcdfShuffleFlag(0)
cdms.setNetcdfDeflateFlag(0)
cdms.setNetcdfDeflateLevelFlag(0)

# exp = 'historical'
exp = "amip"

MIP = "cmip6"  # 'CMIP6'
# MIP = 'cmip5'   # 'CMIP5'

if MIP == "cmip6":
    ver = "v20230324"
if MIP == "cmip5":
    ver = "v20230324"

# NEED TO RUN SEPERATELY FOR LW AND SW (i.e., rsut and rlut)
# radvar = 'rsut'
radvar = "rlut"

pit = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/"
    + MIP
    + "/"
    + exp
    + "/"
    + ver
    + "/"
)
pi = pit + radvar + "cs/"

lst = sorted(glob.glob(pi + "*" + radvar + "cs" "*.nc"))

for lc in lst:
    try:
        li = lc.replace(radvar + "cs", radvar)

        if os.path.isfile(li):
            if radvar == "rsut":
                fixname = "rstcre"
            elif radvar == "rlut":
                fixname = "rltcre"

            os.makedirs(pi.replace(radvar + "cs", fixname), exist_ok=True)

            f = cdms.open(li)
            d = f(radvar)
            fc = cdms.open(lc)
            att_keys = fc.attributes.keys()
            dc = fc(radvar + "cs")
            f.close()
            fc.close()

            dgrid = d.getGrid()

            cre = MV.subtract(dc, d)
            cre.setGrid(dgrid)

            cre.id = fixname

            cre.units = "W m-2"

            lo = li.replace(radvar, fixname)

            g = cdms.open(lo, "w+")
            for att in f.attributes.keys():
                setattr(g, att, f.attributes[att])
            g.write(cre)
            g.close()

            print("done with ", lo)

            if radvar == "rsut":
                l1 = lc.replace("rsutcs", "rsdt")

            try:
                f1 = cdms.open(l1)
                d1 = f1("rsdt")
                # dif = -1.*d1
                dif = MV.subtract(d1, d)

                dif.units = "W m-2"
                dif.id = "rst"

                l2 = l1.replace("rsdt", "rst")

                os.makedirs(pit + "/rst", exist_ok=True)

                print("starting ", l2)

                g = cdms.open(l2, "w+")

                for att in f1.attributes.keys():
                    setattr(g, att, f1.attributes[att])
                g.write(dif)

                att_keys = f1.attributes.keys()
                att_dic = {}
                g.close()
                f1.close()

            except Exception:
                print("no rsdt ")  # for ', l1

            # ### AND FINALLY, THE NET
            try:
                lw = l2.replace("rst", "rlut")
                f3 = cdms.open(lw)
                d3 = f3("rlut")

                net = MV.subtract(dif, d3)
                net.id = "rt"

                os.makedirs(pit + "/rt", exist_ok=True)

                ln = lw.replace("rlut", "rt")

                g3 = cdms.open(ln, "w+")
                for att in f3.attributes.keys():
                    setattr(g3, att, f3.attributes[att])

                g3.write(net)
                print("done with ", ln)
                f3.close()
                g3.close()
            except Exception:
                print("not working for ", lc)
    except Exception:
        print("not working for -----", lc)
    pass
