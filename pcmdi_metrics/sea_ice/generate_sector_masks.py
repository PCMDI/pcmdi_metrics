import os
import string
import sys

import cdms2
import MV2 as MV
from sector_mask_defs import *

from pcmdi_metrics.pcmdi.pmp_parser import *

P = PMPParser()

P.add_argument(
    "--mp",
    "--modpath",
    type=str,
    dest="modpath",
    default="",
    help="Explicit path to model monthly PR climatology",
)
P.add_argument(
    "-o",
    "--obspath",
    type=str,
    dest="obspath",
    default="",
    help="Explicit path to obs monthly PR climatology",
)
P.add_argument(
    "--outpd",
    "--outpathdata",
    type=str,
    dest="outpathdata",
    default="/export/gleckler1/processing/metrics_package/my_test/sea_ice/git_data/",
    help="Output path for sector scale masks",
)

args = P.parse_args(sys.argv[1:])
sec_mask_dir = args.outpathdata

# Factors
factor1 = 1.0e-6  # model units are m^2, converting to km^2
factor2 = 1.0e-2  # model units are %, converting to non-dimen
a = 6371.009  # Earth radii in km
pi = 22.0 / 7.0
factor3 = 4.0 * pi * a * a  # Earth's surface area in km2
dc = 0.15  # minimum ice concentration contour

pin = "/work/gleckler1/processed_data/cmip5clims-historical/sic/cmip5.MOD.historical.r1i1p1.mo.seaIce.OImon.sic.ver-1.1980-2005.SC.nc"

pins = string.replace(pin, "MOD", "*")

lst = os.popen("ls " + pins).readlines()

mods = []
mods_failed = []
for li in lst:
    mod = string.split(li, ".")[1]
    if mod not in mods:
        mods.append(mod)

# w =sys.stdin.readline()

var = "sic"
factor2 = 1

mods = ["ACCESS1-3"]

for mod in mods:
    try:
        fc = string.replace(pin, "MOD", mod)
        f = cdms2.open(fc)
        sic = f(var, squeeze=1)
        sic_grid = sic.getGrid()
        lat = sic.getLatitude()
        lon = sic.getLongitude()
        sic = MV.multiply(sic, factor2)

        print("CMIP5-native= ", MV.max(sic))
        if MV.rank(lat) == 1:
            tmp2d = f(var, time=slice(0, 1), squeeze=1)
            lats = MV.zeros(tmp2d.shape)
            for ii in range(0, len(lon)):
                lats[:, ii] = lat[:]
        else:
            lats = lat

        if MV.rank(lon) == 1:
            tmp2d = f(var, time=slice(0, 1), squeeze=1)
            lons = MV.zeros(tmp2d.shape)
            for ii in range(0, len(lat)):
                lons[ii, :] = lon[:]
        else:
            lons = lon

        f.close()

        #######################################################
        ### areacello
        area_dir = "/work/cmip5/fx/fx/areacello/"
        alist = os.listdir(area_dir)  # LIST OF ALL AREACELLO FILES

        for a in alist:
            if string.find(a, mod) != -1:
                areaf = a
                print(mod, " ", a)

        #  w = sys.stdin.readline()

        g = cdms2.open(area_dir + areaf)

        try:
            area = g("areacello")
        except:
            area = g("areacella")
        area = MV.multiply(area, factor1)
        area = MV.multiply(area, factor1)

        g.close()

        land_mask = MV.zeros(area.shape)

        # Reading the ocean/land grid cell masks (sftof/sftlf)
        mask_dir = "/work/cmip5/fx/fx/sftof/"
        mlist = os.listdir(mask_dir)  # LIST OF ALL AREACELLO FILES

        for m in mlist:
            if string.find(m, mod) != -1:
                maskf = m
                print(mod, " ", m)

        s = cdms2.open(mask_dir + maskf)
        try:
            frac = s("sftof")
            if (
                mod != "MIROC5"
                and mod != "GFDL-CM2p1"
                and mod != "GFDL-CM3"
                and mod != "GFDL-ESM2M"
            ):
                frac = MV.multiply(frac, factor2)
                print(mod, MV.max(frac))
            area = MV.multiply(area, frac)
            land_mask = MV.multiply(1, (1 - frac))
        except:
            frac = s("sftlf")
        if (
            mod != "MIROC5"
            or mod != "GFDL-CM2p1"
            or mod != "GFDL-CM3"
            or mod != "GFDL-ESM2M"
        ):
            frac = MV.multiply(frac, factor2)
        area = MV.multiply(area, (1 - frac))
        land_mask = MV.multiply(1, frac)
        s.close()

        # Creating regional masks
        # GFDL and bcc model grids have shift of 80
        if mod[0:4] == "GFDL" or mod[0:3] == "bcc":
            lons_a = MV.where(MV.less(lons, -180.0), lons + 360.0, lons)
            lons_p = MV.where(MV.less(lons, 0.0), lons + 360.0, lons)
        else:
            lons_a = MV.where(MV.greater(lons, 180.0), lons - 360.0, lons)
            lons_p = lons

        print("CMIP5")
        print("lons_na= ", MV.min(lons_a), MV.max(lons_a))
        print("lons_np= ", MV.min(lons_p), MV.max(lons_p))
        #  mask_arctic=MV.zeros(area.shape)
        #      mask_antarctic=MV.zeros(area.shape)
        mask_ca = MV.zeros(area.shape)
        mask_na = MV.zeros(area.shape)
        mask_np = MV.zeros(area.shape)
        mask_sa = MV.zeros(area.shape)
        mask_sp = MV.zeros(area.shape)
        mask_io = MV.zeros(area.shape)

        ###############################################################

        sectors = ["ca", "na", "np", "sp", "sa", "io"]

        for sector in sectors:
            mask = getmask(sector, lats, lons, lons_a, lons_p, land_mask)

            g = cdms2.open(sec_mask_dir + "mask_" + mod + "_" + sector + ".nc", "w+")
            mask.id = "mask"
            g.write(mask)
            #  land_mask.id = 'sftof'
            #  g.write(land_mask)
            g.close()

        print("got it!", " ", mask.shape)
        w = sys.stdin.readline()

        # Calculate the Total Sea Ice Concentration/Extent/Area
        #       ice_area = MV.multiply(sic,1)                                #SIC
        area = MV.multiply(1, area)  # SIE
        ice_area = MV.multiply(sic, area)  # SIA
        ice_area = MV.where(
            MV.greater_equal(sic, 0.15), ice_area, 0.0
        )  # Masking out the sic<0.15

        #    arctic=MV.logical_and(MV.greater_equal(lats,35.),MV.less(lats,87.2))         #SSM/I limited to 87.2N
        mask_arctic = MV.logical_and(
            MV.greater_equal(lats, 45.0), MV.less(lats, 90.0)
        )  # Adding currently in SSM/I 100% in the area >87.2N
        mask_antarctic = MV.logical_and(
            MV.greater_equal(lats, -90.0), MV.less(lats, -55.0)
        )

    except:
        "Failed for ", mod
        mods_failed.append(mod)

print("failed for ", mods_failed)

# Calculate the Sea Ice Covered Area
