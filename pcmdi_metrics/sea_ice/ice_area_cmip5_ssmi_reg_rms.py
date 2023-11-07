import cdms2 as cdms
import cdtime
import cdutil
import genutil
import matplotlib.pyplot as plt
import MV2 as MV
import numpy as np


def tgrid(t):
    import cdtime

    time = t[:] * 0.0
    if t[0] == 0.0:
        dt = 0.0
    else:
        dt = 0.5  # centered in the midlle of the month
    time[0] = dt / 12.0
    nmonths = len(t)  # monthy time series

    for it in range(1, nmonths):
        time[it] = time[it - 1] + 1.0 / 12.0

    time = time + cdtime.reltime(t[0], t.units).tocomp().year

    return time


value = 0
cdms.setNetcdfShuffleFlag(value)
cdms.setNetcdfDeflateFlag(value)
cdms.setNetcdfDeflateLevelFlag(value)

cdms.setAutoBounds("on")

# Factors
factor1 = 1.0e-6  # model units are m^2, converting to km^2
factor2 = 1.0e-2  # model units are %, converting to non-dimen
a = 6371.009  # Earth radii in km
pi = 22.0 / 7.0
factor3 = 4.0 * pi * a * a  # Earth's surface area in km2
dc = 0.15  # minimum ice concentration contour


# Observations
dlist_n = ["ssmi_nt_n_names.asc", "ssmi_bt_n_names.asc"]
dlist_s = ["ssmi_nt_s_names.asc", "ssmi_bt_s_names.asc"]

annual_cycle_obs_arctic = []
annual_cycle_obs_antarctic = []
data_n = MV.zeros([324])
obs_n = MV.zeros([324, 2])
ta_ca = MV.zeros([324])
obs_ca = MV.zeros([324, 2])
ta_na = MV.zeros([324])
obs_na = MV.zeros([324, 2])
ta_np = MV.zeros([324])
obs_np = MV.zeros([324, 2])
data_s = MV.zeros([324])
obs_s = MV.zeros([324, 2])
ta_sa = MV.zeros([324])
obs_sa = MV.zeros([324, 2])
ta_sp = MV.zeros([324])
obs_sp = MV.zeros([324, 2])
ta_io = MV.zeros([324])
obs_io = MV.zeros([324, 2])

# SSM/I Arctic

for dl in range(0, len(dlist_n)):
    f = open(dlist_n[dl])
    lines_n = f.readlines()
    f.close

    # Reading the ocean/ice grid cell area (area)
    # Reading the sea ice concentration (ice_con)
    for i in range(0, len(lines_n)):
        filename = lines_n[i].strip("\t\n\r")
        print(filename)
        obs = cdms.open(filename)
        lats_n = obs("lat")
        lons_n = obs("lon")
        area_n = obs("area")
        sic_n = obs("ice_con")
        sic_n = MV.multiply(sic_n, factor2)
        area_n = MV.multiply(area_n, factor1)

        obs.close()

        # Creating regional masks
        lons_p = MV.where(MV.less(lons_n, 0.0), lons_n + 360.0, lons_n)
        lons_a = lons_n

        print("Obs")
        print("lons_na= ", MV.min(lons_a), MV.max(lons_a))
        print("lons_np= ", MV.min(lons_p), MV.max(lons_p))

        mask_ca = MV.zeros(area_n.shape)
        mask_na = MV.zeros(area_n.shape)
        mask_np = MV.zeros(area_n.shape)

        # Arctic Regions
        # Central Arctic
        lat_bound1 = MV.logical_and(
            MV.greater(lats_n, 80.0), MV.less_equal(lats_n, 87.2)
        )
        lat_bound2 = MV.logical_and(
            MV.greater(lats_n, 65.0), MV.less_equal(lats_n, 87.2)
        )
        lat_bound3 = MV.logical_and(
            MV.greater(lats_n, 87.2), MV.less_equal(lats_n, 90.0)
        )
        lon_bound1 = MV.logical_and(
            MV.greater(lons_a, -120.0), MV.less_equal(lons_a, 90.0)
        )
        lon_bound2 = MV.logical_and(
            MV.greater(lons_p, 90.0), MV.less_equal(lons_p, 240.0)
        )
        reg1_ca = MV.logical_and(lat_bound1, lon_bound1)
        reg2_ca = MV.logical_and(lat_bound2, lon_bound2)
        mask_ca = MV.where(MV.logical_or(reg1_ca, reg2_ca), 1, 0)
        mask_pole = MV.where(lat_bound3, 1, 0)

        # NA region
        lat_bound = MV.logical_and(
            MV.greater(lats_n, 35.0), MV.less_equal(lats_n, 80.0)
        )
        lon_bound = MV.logical_and(
            MV.greater(lons_a, -120.0), MV.less_equal(lons_a, 90.0)
        )
        mask_na = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # NP region
        lat_bound = MV.logical_and(
            MV.greater(lats_n, 35.0), MV.less_equal(lats_n, 65.0)
        )
        lon_bound = MV.logical_and(
            MV.greater(lons_p, 90.0), MV.less_equal(lons_p, 240.0)
        )
        mask_np = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        area_sic_pole = MV.where(MV.equal(mask_pole, True), MV.multiply(1, area_n), 0.0)

        # Masking out sic<0.15
        ice_area = MV.where(
            MV.greater_equal(sic_n, 0.15), area_n, 0.0
        )  # Masking out sic<0.15

        # Ice Extent
        #    area_sic_arctic=MV.multiply(1,ice_area)
        #    area_sic_ca=MV.where(MV.equal(mask_ca,True),MV.multiply(1,ice_area),0.)
        #    area_sic_na=MV.where(MV.equal(mask_na,True),MV.multiply(1,ice_area),0.)
        #    area_sic_np=MV.where(MV.equal(mask_np,True),MV.multiply(1,ice_area),0.)
        # Ice Area
        area_sic_arctic = MV.multiply(sic_n, ice_area)
        area_sic_ca = MV.where(
            MV.equal(mask_ca, True), MV.multiply(sic_n, ice_area), 0.0
        )
        area_sic_na = MV.where(
            MV.equal(mask_na, True), MV.multiply(sic_n, ice_area), 0.0
        )
        area_sic_np = MV.where(
            MV.equal(mask_np, True), MV.multiply(sic_n, ice_area), 0.0
        )

        data_n[i] = MV.add(MV.sum(area_sic_arctic), MV.sum(area_sic_pole))
        ta_ca[i] = MV.add(MV.sum(area_sic_ca), MV.sum(area_sic_pole))
        ta_na[i] = MV.sum(area_sic_na)
        ta_np[i] = MV.sum(area_sic_np)

        print("data_n= ", data_n[i])
        print("ta_na= ", ta_na[i])
        print("ta_np= ", ta_np[i])

        print(MV.average(sic_n))

    obs_n[:, dl] = MV.array(data_n, id="sic")
    obs_ca[:, dl] = MV.array(ta_ca, id="sic")
    obs_na[:, dl] = MV.array(ta_na, id="sic")
    obs_np[:, dl] = MV.array(ta_np, id="sic")

# SSM/I Antarctic
for dl in range(0, len(dlist_s)):
    g = open(dlist_s[dl])
    lines_s = g.readlines()
    g.close

    for i in range(0, len(lines_s)):
        filename = lines_s[i].strip("\t\n\r")
        print(filename)
        obs = cdms.open(filename)
        lats_s = obs("lat")
        lons_s = obs("lon")
        area_s = obs("area")
        sic_s = obs("ice_con")
        sic_s = MV.multiply(sic_s, factor2)
        area_s = MV.multiply(area_s, factor1)

        obs.close()

        # Creating regional masks
        lons_sa = lons_s
        lons_sp = MV.where(MV.less(lons_s, 0.0), lons_s + 360, lons_s)
        lons_io = lons_sp

        print("Obs")
        print("lons_sa= ", MV.min(lons_sa), MV.max(lons_sa))
        print("lons_sp= ", MV.min(lons_sp), MV.max(lons_sp))

        mask_sa = MV.zeros(area_s.shape)
        mask_sp = MV.zeros(area_s.shape)
        mask_io = MV.zeros(area_s.shape)

        # Antarctic Regions
        lat_bound = MV.logical_and(
            MV.greater(lats_s, -90.0), MV.less_equal(lats_s, -40.0)
        )

        # SA region
        #    lon_bound=MV.logical_and(MV.greater(lons_sa,-60.),MV.less_equal(lons_sa,30.))
        lon_bound = MV.logical_and(
            MV.greater(lons_sa, -60.0), MV.less_equal(lons_sa, 20.0)
        )
        mask_sa = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # SP region
        #    lon_bound=MV.logical_and(MV.greater(lons_sp,130.),MV.less_equal(lons_sp,300.))
        lon_bound = MV.logical_and(
            MV.greater(lons_sp, 90.0), MV.less_equal(lons_sp, 300.0)
        )
        mask_sp = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # Indian Ocean (IO) region
        #    lon_bound=MV.logical_and(MV.greater(lons_sp,30.),MV.less_equal(lons_sp,130.))
        lon_bound = MV.logical_and(
            MV.greater(lons_sp, 20.0), MV.less_equal(lons_sp, 90.0)
        )
        mask_io = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # Masking out sic<0.15
        ice_area = MV.where(
            MV.greater_equal(sic_s, dc), area_s, 0.0
        )  # Masking out sic<0.15
        # Ice Extent
        #    area_sic_antarctic=MV.multiply(1,ice_area)
        #    area_sic_sa=MV.where(MV.equal(mask_sa,True),MV.multiply(1,ice_area),0.)
        #    area_sic_sp=MV.where(MV.equal(mask_sp,True),MV.multiply(1,ice_area),0.)
        #    area_sic_io=MV.where(MV.equal(mask_io,True),MV.multiply(1,ice_area),0.)
        # Ice Area
        area_sic_antarctic = MV.multiply(sic_s, ice_area)
        area_sic_sa = MV.where(MV.equal(mask_sa, True), MV.multiply(sic_s, area_s), 0.0)
        area_sic_sp = MV.where(MV.equal(mask_sp, True), MV.multiply(sic_s, area_s), 0.0)
        area_sic_io = MV.where(MV.equal(mask_io, True), MV.multiply(sic_s, area_s), 0.0)

        data_s[i] = MV.sum(area_sic_antarctic)
        ta_sa[i] = MV.sum(area_sic_sa)
        ta_sp[i] = MV.sum(area_sic_sp)
        ta_io[i] = MV.sum(area_sic_io)

        print(MV.average(sic_s))

    obs_s[:, dl] = MV.array(data_s, id="sic")
    obs_s = MV.masked_equal(obs_s, -9999.0)
    obs_sa[:, dl] = MV.array(ta_sa, id="sic")
    obs_sp[:, dl] = MV.array(ta_sp, id="sic")
    obs_io[:, dl] = MV.array(ta_io, id="sic")

# Create Time Axis
years = []
months = []
for iy in range(1979, 2006):
    for im in range(1, 13):
        years.append(int(iy))
        months.append(int(im))

timeax = []
for date in zip(years, months):
    yr, mo = date
    print(yr)
    c = cdtime.comptime(yr, mo)
    print(c)
    print(c.torel("days since 1979-1-1").value)
    timeax = timeax + [int(c.torel("days since 1979-1-1").value)]

time = cdms.createAxis(timeax)
time.id = "time"
time.units = "days since 1979-1-1"
bounds = cdutil.times.setAxisTimeBoundsMonthly(time)
obs_n.setAxis(0, time)
obs_ca.setAxis(0, time)
obs_na.setAxis(0, time)
obs_np.setAxis(0, time)
obs_s.setAxis(0, time)
obs_sa.setAxis(0, time)
obs_sp.setAxis(0, time)
obs_io.setAxis(0, time)

# Calculate Annual Cycle (1979-2005)
cdutil.setTimeBoundsMonthly(obs_n)
cdutil.setTimeBoundsMonthly(obs_s)
annual_cycle_obs_arctic = np.array(cdutil.ANNUALCYCLE.climatology(obs_n[0:324]))
annual_cycle_obs_ca = np.array(cdutil.ANNUALCYCLE.climatology(obs_ca[0:324]))
annual_cycle_obs_na = np.array(cdutil.ANNUALCYCLE.climatology(obs_na[0:324]))
annual_cycle_obs_np = np.array(cdutil.ANNUALCYCLE.climatology(obs_np[0:324]))
annual_cycle_obs_antarctic = np.array(cdutil.ANNUALCYCLE.climatology(obs_s[0:324]))
annual_cycle_obs_sa = np.array(cdutil.ANNUALCYCLE.climatology(obs_sa[0:324]))
annual_cycle_obs_sp = np.array(cdutil.ANNUALCYCLE.climatology(obs_sp[0:324]))
annual_cycle_obs_io = np.array(cdutil.ANNUALCYCLE.climatology(obs_io[0:324]))

annual_cycle_std_obs_arctic = np.zeros((12, 2))
annual_cycle_std_obs_ca = np.zeros((12, 2))
annual_cycle_std_obs_na = np.zeros((12, 2))
annual_cycle_std_obs_np = np.zeros((12, 2))
annual_cycle_std_obs_antarctic = np.zeros((12, 2))
annual_cycle_std_obs_sa = np.zeros((12, 2))
annual_cycle_std_obs_sp = np.zeros((12, 2))
annual_cycle_std_obs_io = np.zeros((12, 2))

for im in range(0, 12):
    annual_cycle_std_obs_arctic[im, :] = np.array(
        genutil.statistics.std(obs_n[im:324:12, :])
    )
    annual_cycle_std_obs_ca[im, :] = np.array(
        genutil.statistics.std(obs_ca[im:324:12, :])
    )
    annual_cycle_std_obs_na[im, :] = np.array(
        genutil.statistics.std(obs_na[im:324:12, :])
    )
    annual_cycle_std_obs_np[im, :] = np.array(
        genutil.statistics.std(obs_np[im:324:12, :])
    )
    annual_cycle_std_obs_antarctic[im, :] = np.array(
        genutil.statistics.std(obs_s[im:324:12, :])
    )
    annual_cycle_std_obs_sa[im, :] = np.array(
        genutil.statistics.std(obs_sa[im:324:12, :])
    )
    annual_cycle_std_obs_sp[im, :] = np.array(
        genutil.statistics.std(obs_sp[im:324:12, :])
    )
    annual_cycle_std_obs_io[im, :] = np.array(
        genutil.statistics.std(obs_io[im:324:12, :])
    )


# NSIDC-0192
# SSM/I Arctic
# Area
dlist_n = [
    "nasateam/gsfc.nasateam.month.area.1978-2010.n.asc",
    "bootstrap/gsfc.bootstrap.month.area.1978-2010.n.asc",
]
dlist_s = [
    "nasateam/gsfc.nasateam.month.area.1978-2010.s.asc",
    "bootstrap/gsfc.bootstrap.month.area.1978-2010.s.asc",
]
# Extent
# dlist_n=['nasateam/gsfc.nasateam.month.extent.1978-2010.n.asc','bootstrap/gsfc.bootstrap.month.extent.1978-2010.n.asc']
# dlist_s=['nasateam/gsfc.nasateam.month.extent.1978-2010.s.asc','bootstrap/gsfc.bootstrap.month.extent.1978-2010.s.asc']
obs1_n = MV.zeros([324, 2])
obs1_ca = MV.zeros([324, 2])
obs1_na = MV.zeros([324, 2])
obs1_np = MV.zeros([324, 2])
obs1_s = MV.zeros([324, 2])
obs1_sa = MV.zeros([324, 2])
obs1_sp = MV.zeros([324, 2])
obs1_io = MV.zeros([324, 2])

for dl in range(0, len(dlist_n)):
    years = []
    months = []
    data_n = []
    data_ca = []
    data_na = []
    data_np = []
    data_s = []
    data_sa = []
    data_sp = []
    data_io = []

    f = open("/export/ivanova2/IceData/AreaExtent/NSIDC-0192/ice-extent/" + dlist_n[dl])
    lines_n = f.readlines()
    f.close

    g = open("/export/ivanova2/IceData/AreaExtent/NSIDC-0192/ice-extent/" + dlist_s[dl])
    lines_s = g.readlines()
    g.close

    for line in lines_n:
        #    val1,val2,val3i,val4,val5=map(int,line.split())
        sp = line.split()
        try:
            val0 = int(sp[0])
            val1 = int(sp[1])
            val3 = float(sp[3])
            val4 = float(sp[4])
            val5 = float(sp[5])
            val6 = float(sp[6])
            val7 = float(sp[7])
            val8 = float(sp[8])
            val9 = float(sp[9])
            val10 = float(sp[10])
            val11 = float(sp[11])
            val12 = float(sp[12])
            years.append(val0)
            months.append(val1)
            data_n.append(val3)
            data_np.append(val4 + val5)
            data_na.append(val6 + val7 + val8 + val9 + val11 + val12)
            data_ca.append(val10)
        except:
            pass
    obs1_n[:, dl] = MV.array(data_n[0:324], id="sic")
    obs1_ca[:, dl] = MV.array(data_ca[0:324], id="sic")
    obs1_na[:, dl] = MV.array(data_na[0:324], id="sic")
    obs1_np[:, dl] = MV.array(data_np[0:324], id="sic")

    for line in lines_s:
        sp = line.split()
        try:
            val3 = float(sp[3])
            val4 = float(sp[4])
            val5 = float(sp[5])
            val6 = float(sp[6])
            val7 = float(sp[7])
            val8 = float(sp[8])
            data_s.append(val3)
            data_sa.append(val4)
            data_io.append(val5)
            data_sp.append(val6 + val7 + val8)
        except:
            pass

    obs1_s[:, dl] = MV.array(data_s[0:324], id="sic")
    obs1_sa[:, dl] = MV.array(data_sa[0:324], id="sic")
    obs1_sp[:, dl] = MV.array(data_sp[0:324], id="sic")
    obs1_io[:, dl] = MV.array(data_io[0:324], id="sic")

obs1_n = MV.masked_equal(obs1_n, -999.0)
obs1_ca = MV.masked_equal(obs1_ca, -999.0)
obs1_na = MV.masked_equal(obs1_na, -999.0)
obs1_np = MV.masked_equal(obs1_np, -999.0)
obs1_s = MV.masked_equal(obs1_s, -999.0)
obs1_sa = MV.masked_equal(obs1_sa, -999.0)
obs1_sp = MV.masked_equal(obs1_sp, -999.0)
obs1_io = MV.masked_equal(obs1_io, -999.0)
obs1_n = MV.multiply(obs1_n, factor1)
obs1_ca = MV.multiply(obs1_ca, factor1)
obs1_np = MV.multiply(obs1_np, factor1)
obs1_na = MV.multiply(obs1_na, factor1)
obs1_s = MV.multiply(obs1_s, factor1)
obs1_sa = MV.multiply(obs1_sa, factor1)
obs1_sp = MV.multiply(obs1_sp, factor1)
obs1_io = MV.multiply(obs1_io, factor1)


# Create Time Axis
timeax = []
for date in zip(years, months):
    yr, mo = date
    print(yr)
    c = cdtime.comptime(yr, mo)
    print(c)
    print(c.torel("days since 1979-1-1").value)
    timeax = timeax + [int(c.torel("days since 1979-1-1").value)]

time = cdms.createAxis(timeax[0:324])
time.id = "time"
time.units = "days since 1979-1-1"
bounds = cdutil.times.setAxisTimeBoundsMonthly(time)
obs1_n.setAxis(0, time)
obs1_ca.setAxis(0, time)
obs1_na.setAxis(0, time)
obs1_np.setAxis(0, time)
obs1_s.setAxis(0, time)
obs1_sa.setAxis(0, time)
obs1_sp.setAxis(0, time)
obs1_io.setAxis(0, time)


# Calculate Annual Cycle (1979-2005)
cdutil.setTimeBoundsMonthly(obs1_n)
cdutil.setTimeBoundsMonthly(obs1_s)
annual_cycle_obs1_arctic = np.array(cdutil.ANNUALCYCLE.climatology(obs1_n[0:324]))
annual_cycle_obs1_ca = np.array(cdutil.ANNUALCYCLE.climatology(obs1_ca[0:324]))
annual_cycle_obs1_na = np.array(cdutil.ANNUALCYCLE.climatology(obs1_na[0:324]))
annual_cycle_obs1_np = np.array(cdutil.ANNUALCYCLE.climatology(obs1_np[0:324]))
annual_cycle_obs1_antarctic = np.array(cdutil.ANNUALCYCLE.climatology(obs1_s[0:324]))
annual_cycle_obs1_sa = np.array(cdutil.ANNUALCYCLE.climatology(obs1_sa[0:324]))
annual_cycle_obs1_sp = np.array(cdutil.ANNUALCYCLE.climatology(obs1_sp[0:324]))
annual_cycle_obs1_io = np.array(cdutil.ANNUALCYCLE.climatology(obs1_io[0:324]))

annual_cycle_std_obs1_arctic = np.zeros((12, 2))
annual_cycle_std_obs1_ca = np.zeros((12, 2))
annual_cycle_std_obs1_na = np.zeros((12, 2))
annual_cycle_std_obs1_np = np.zeros((12, 2))
annual_cycle_std_obs1_antarctic = np.zeros((12, 2))
annual_cycle_std_obs1_sa = np.zeros((12, 2))
annual_cycle_std_obs1_sp = np.zeros((12, 2))
annual_cycle_std_obs1_io = np.zeros((12, 2))

for im in range(0, 12):
    annual_cycle_std_obs1_arctic[im, :] = np.array(
        genutil.statistics.std(obs1_n[im:324:12, :])
    )
    annual_cycle_std_obs1_ca[im, :] = np.array(
        genutil.statistics.std(obs1_ca[im:324:12, :])
    )
    annual_cycle_std_obs1_na[im, :] = np.array(
        genutil.statistics.std(obs1_na[im:324:12, :])
    )
    annual_cycle_std_obs1_np[im, :] = np.array(
        genutil.statistics.std(obs1_np[im:324:12, :])
    )
    annual_cycle_std_obs1_antarctic[im, :] = np.array(
        genutil.statistics.std(obs1_s[im:324:12, :])
    )
    annual_cycle_std_obs1_sa[im, :] = np.array(
        genutil.statistics.std(obs1_sa[im:324:12, :])
    )
    annual_cycle_std_obs1_sp[im, :] = np.array(
        genutil.statistics.std(obs1_sp[im:324:12, :])
    )
    annual_cycle_std_obs1_io[im, :] = np.array(
        genutil.statistics.std(obs1_io[im:324:12, :])
    )

# Calculate the Obs RMS
rms_arctic_obs1 = genutil.statistics.rms(
    annual_cycle_obs1_arctic[:, 1], annual_cycle_obs1_arctic[:, 0], axis=0
)
rms_antarctic_obs1 = genutil.statistics.rms(
    annual_cycle_obs1_antarctic[:, 1], annual_cycle_obs1_antarctic[:, 0], axis=0
)
rms_ca_obs1 = genutil.statistics.rms(
    annual_cycle_obs1_ca[:, 1], annual_cycle_obs1_ca[:, 0], axis=0
)
rms_na_obs1 = genutil.statistics.rms(
    annual_cycle_obs1_na[:, 1], annual_cycle_obs1_na[:, 0], axis=0
)
rms_np_obs1 = genutil.statistics.rms(
    annual_cycle_obs1_np[:, 1], annual_cycle_obs1_np[:, 0], axis=0
)
rms_sa_obs1 = genutil.statistics.rms(
    annual_cycle_obs1_sa[:, 1], annual_cycle_obs1_sa[:, 0], axis=0
)
rms_sp_obs1 = genutil.statistics.rms(
    annual_cycle_obs1_sp[:, 1], annual_cycle_obs1_sp[:, 0], axis=0
)
rms_io_obs1 = genutil.statistics.rms(
    annual_cycle_obs1_io[:, 1], annual_cycle_obs1_io[:, 0], axis=0
)


# CMIP5 Native grid
var = "sic"
# obs = ['NASATEAM','BOOTSTRAP']
# mods = ['Obs-NASATEAM','Obs-BOOTSTRAP','CMIP5 Native grid','CMIP5 Interpolated']
mods_obs = ["CMIP5 MME", "Obs-NASATEAM", "Obs-BOOTSTRAP"]
obs_mods = ["Obs-NASATEAM", "Obs-BOOTSTRAP", "CMIP5 MME Native grid"]
lines_m = [
    "ro-",
    "rd-",
    "ro--",
    "co-",
    "c*-",
    "cd-",
    "c-",
    "bo-",
    "b^-",
    "b*-",
    "co--",
    "go--",
    "g^--",
    "gd--",
    "g-",
    "m*--",
    "y*-",
]  # ,'m^-','yo--']
# lines_d = ['bo-','g*-']
# cols_d=['b','g']

flist = open("./cmip5_sic_names_all_xml_012413_conserv.asc")
# flist=open('./cmip5_sic_names_all_xml_012413_conserv_ccsm4.asc')
# flist=open('./cmip5_sic_names_all_xml_121212_conserv.asc')
# flist=open('./cmip5_sic_names_all_xml_121212_ncar.asc')
# flist=open('./cmip5_sic_names_all_xml_121212.asc')
# flist=open('./cmip5_sic_names_all_xml_102412_hadgem.asc')
fnames = flist.readlines()


glist = open("./cmip5_areacell_names_nc_012413_conserv.asc")
# glist=open('./cmip5_areacell_names_nc_012413_conserv_ccsm4.asc')
# glist=open('./cmip5_areacell_names_nc.asc')
# glist=open('./cmip5_areacell_names_all_xml_121212.asc')
# glist=open('./cmip5_areacell_names_all_xml_121212.asc')
# glist=open('./cmip5_areacell_names_all_xml_010813_conserv.asc')
# glist=open('./cmip5_areacell_names_all_xml_121212_conserv.asc')
# glist=open('./cmip5_areacell_names_all_xml_121212_ncar.asc')
# glist=open('./cmip5_areacell_names_all_xml_102412_hadgem.asc')
gnames = glist.readlines()


# Dictionary with the model names and runs and versions
mod_runs = {}
mods = []
for i in range(0, len(fnames)):
    sp = fnames[i].split(".")
    if sp[3] == "r1i1p1":
        mods.append(sp[1])
for mod in mods:
    runs = []
    vers = []
    for i in range(0, len(fnames)):
        rn = fnames[i].split(".")
        if rn[1] == mod:
            runs.append(rn[3])
            vers.append(rn[7].strip("\t\n\r"))
    mod_runs[mod] = [runs, vers]
    del runs
    del vers

ann_arctic = np.zeros((12, len(mods)))
ann_antarctic = np.zeros((12, len(mods)))
ann_ca = np.zeros((12, len(mods)))
ann_na = np.zeros((12, len(mods)))
ann_np = np.zeros((12, len(mods)))
ann_sa = np.zeros((12, len(mods)))
ann_sp = np.zeros((12, len(mods)))
ann_io = np.zeros((12, len(mods)))
std_arctic = np.zeros((324, len(mods)))
std_antarctic = np.zeros((324, len(mods)))
std_ca = np.zeros((324, len(mods)))
std_na = np.zeros((324, len(mods)))
std_np = np.zeros((324, len(mods)))
std_sa = np.zeros((324, len(mods)))
std_sp = np.zeros((324, len(mods)))
std_io = np.zeros((324, len(mods)))
annual_cycle_std_mod_arctic = np.zeros((12))
annual_cycle_std_mod_antarctic = np.zeros((12))
annual_cycle_std_mod_ca = np.zeros((12))
annual_cycle_std_mod_na = np.zeros((12))
annual_cycle_std_mod_np = np.zeros((12))
annual_cycle_std_mod_sa = np.zeros((12))
annual_cycle_std_mod_sp = np.zeros((12))
annual_cycle_std_mod_io = np.zeros((12))
ann_arctic_mma = np.zeros((12))
ann_antarctic_mma = np.zeros((12))
ann_ca_mma = np.zeros((12))
ann_na_mma = np.zeros((12))
ann_np_mma = np.zeros((12))
ann_sa_mma = np.zeros((12))
ann_sp_mma = np.zeros((12))
ann_io_mma = np.zeros((12))
rms_ann_arctic = np.zeros((len(dlist_n), len(mods)))
rms_ann_antarctic = np.zeros((len(dlist_s), len(mods)))
rms_ann_ca = np.zeros((len(dlist_n), len(mods)))
rms_ann_na = np.zeros((len(dlist_n), len(mods)))
rms_ann_np = np.zeros((len(dlist_n), len(mods)))
rms_ann_sa = np.zeros((len(dlist_s), len(mods)))
rms_ann_sp = np.zeros((len(dlist_s), len(mods)))
rms_ann_io = np.zeros((len(dlist_s), len(mods)))

nm = 0
i = -1

for mod in mods:
    i = i + 1
    runs = mod_runs[mod][0]
    vers = mod_runs[mod][1]

    # Reading the ocean/ice grid cell area (areacello)
    gfile = gnames[i].strip("\t\n\r")
    print(gfile)
    g = cdms.open(gfile)
    try:
        area = g("areacello")
    except:
        area = g("areacella")
    area = MV.multiply(area, factor1)
    area = MV.multiply(area, factor1)

    g.close()

    total_area_arctic = MV.zeros([324])
    total_area_antarctic = MV.zeros([324])
    total_area_ca = MV.zeros([324])
    total_area_na = MV.zeros([324])
    total_area_np = MV.zeros([324])
    total_area_sa = MV.zeros([324])
    total_area_sp = MV.zeros([324])
    total_area_io = MV.zeros([324])

    nr = 0  # Number fo individual model runs

    for ir in range(0, len(runs)):
        nr = nr + 1
        # Reading the sea ice concentration (sic)
        infile = (
            "/work/cmip5/historical/seaIce/mo/sic/"
            + "cmip5."
            + mod
            + ".historical."
            + runs[ir]
            + ".mo.seaIce.sic."
            + vers[ir]
            + ".xml"
        )
        print(infile)

        f = cdms.open(infile)
        if (
            (mod == "HadGEM2-CC" and (runs[ir] == "r1i1p1" or runs[ir] == "r3i1p1"))
            or mod == "HadGEM2-ES"
            and (runs[ir] == "r2i1p1" or runs[ir] == "r3i1p1" or runs[ir] == "r4i1p1")
        ):
            sic = f(var, time=("1978-12-1", "2006-1-1"))
        else:
            sic = f(var, time=("1979-1-1", "2006-1-1"))
            print(MV.average(sic))
        t = sic.getTime()
        lat = sic.getLatitude()
        lon = sic.getLongitude()
        sic = MV.multiply(sic, factor2)

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

        # Creating regional masks
        lons_a = MV.where(MV.greater(lons, 180.0), lons - 360, lons)
        lons_p = lons
        print("CMIP5")
        print("lons_na= ", MV.min(lons_a), MV.max(lons_a))
        print("lons_np= ", MV.min(lons_p), MV.max(lons_p))
        mask_ca = MV.zeros(area.shape)
        mask_na = MV.zeros(area.shape)
        mask_np = MV.zeros(area.shape)
        mask_sa = MV.zeros(area.shape)
        mask_sp = MV.zeros(area.shape)
        mask_io = MV.zeros(area.shape)

        # Arctic Regions
        # Central Arctic
        #    lat_bound1=MV.logical_and(MV.greater(lats,80.),MV.less_equal(lats,87.2))
        #    lat_bound2=MV.logical_and(MV.greater(lats,65.),MV.less_equal(lats,87.2))
        lat_bound1 = MV.logical_and(MV.greater(lats, 80.0), MV.less_equal(lats, 90.0))
        lat_bound2 = MV.logical_and(MV.greater(lats, 65.0), MV.less_equal(lats, 90.0))
        lon_bound1 = MV.logical_and(
            MV.greater(lons_a, -120.0), MV.less_equal(lons_a, 90.0)
        )
        lon_bound2 = MV.logical_and(
            MV.greater(lons_p, 90.0), MV.less_equal(lons_p, 240.0)
        )
        reg1_ca = MV.logical_and(lat_bound1, lon_bound1)
        reg2_ca = MV.logical_and(lat_bound2, lon_bound2)
        mask_ca = MV.where(MV.logical_or(reg1_ca, reg2_ca), 1, 0)

        # NA region
        lat_bound = MV.logical_and(MV.greater(lats, 35.0), MV.less_equal(lats, 80.0))
        lon_bound = MV.logical_and(
            MV.greater(lons_a, -120.0), MV.less_equal(lons_a, 90.0)
        )
        mask_na = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # NP region
        lat_bound = MV.logical_and(MV.greater(lats, 35.0), MV.less_equal(lats, 65.0))
        lon_bound = MV.logical_and(
            MV.greater(lons_p, 90.0), MV.less_equal(lons_p, 240.0)
        )
        mask_np = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # Antarctic Regions
        lat_bound = MV.logical_and(MV.greater(lats, -90.0), MV.less_equal(lats, -40.0))

        # SA region
        lon_bound = MV.logical_and(
            MV.greater(lons_a, -60.0), MV.less_equal(lons_a, 20.0)
        )
        mask_sa = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # SP region
        #    lon_bound=MV.logical_and(MV.greater(lons_p,130.),MV.less_equal(lons_p,300.))
        lon_bound = MV.logical_and(
            MV.greater(lons_p, 90.0), MV.less_equal(lons_p, 300.0)
        )

        mask_sp = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # IO region
        #    lon_bound=MV.logical_and(MV.greater(lons_p,30.),MV.less_equal(lons_p,130.))
        lon_bound = MV.logical_and(
            MV.greater(lons_p, 20.0), MV.less_equal(lons_p, 90.0)
        )
        mask_io = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)

        # Calculate the Total Sea Ice Area
        ice_area = MV.multiply(sic, area)
        ice_area = MV.where(
            MV.greater_equal(sic, 0.15), ice_area, 0.0
        )  # Masking out the sic<0.15

        #    arctic=MV.logical_and(MV.greater_equal(lats,35.),MV.less(lats,87.2))         #SSM/I limited to 87.2N
        arctic = MV.logical_and(
            MV.greater_equal(lats, 35.0), MV.less(lats, 90.0)
        )  # Adding currently in SSM/I 100% in the area >87.2N
        antarctic = MV.logical_and(MV.greater_equal(lats, -90.0), MV.less(lats, -40.0))

        for nt in range(len(t)):
            aice_arctic = MV.where(MV.equal(arctic, True), ice_area[nt], 0.0)
            aice_antarctic = MV.where(MV.equal(antarctic, True), ice_area[nt], 0.0)
            area_sic_ca = MV.where(MV.equal(mask_ca, True), ice_area[nt], 0.0)
            area_sic_na = MV.where(MV.equal(mask_na, True), ice_area[nt], 0.0)
            area_sic_np = MV.where(MV.equal(mask_np, True), ice_area[nt], 0.0)
            area_sic_sa = MV.where(MV.equal(mask_sa, True), ice_area[nt], 0.0)
            area_sic_sp = MV.where(MV.equal(mask_sp, True), ice_area[nt], 0.0)
            area_sic_io = MV.where(MV.equal(mask_io, True), ice_area[nt], 0.0)
            total_area_arctic[nt] = total_area_arctic[nt] + MV.sum(aice_arctic)
            total_area_antarctic[nt] = total_area_antarctic[nt] + MV.sum(aice_antarctic)
            total_area_ca[nt] = total_area_ca[nt] + MV.sum(area_sic_ca)
            total_area_na[nt] = total_area_na[nt] + MV.sum(area_sic_na)
            total_area_np[nt] = total_area_np[nt] + MV.sum(area_sic_np)
            total_area_sa[nt] = total_area_sa[nt] + MV.sum(area_sic_sa)
            total_area_sp[nt] = total_area_sp[nt] + MV.sum(area_sic_sp)
            total_area_io[nt] = total_area_io[nt] + MV.sum(area_sic_io)

    #        print 'total_area_arctic= ',total_area_arctic[nt]
    #        print 'total_area_na= ',total_area_na[nt]
    #        print 'total_area_np= ',total_area_np[nt]

    # Individual Model Ensemble Mean
    total_area_arctic = MV.divide(total_area_arctic, nr)
    total_area_antarctic = MV.divide(total_area_antarctic, nr)
    total_area_ca = MV.divide(total_area_ca, nr)
    total_area_na = MV.divide(total_area_na, nr)
    total_area_np = MV.divide(total_area_np, nr)
    total_area_sa = MV.divide(total_area_sa, nr)
    total_area_sp = MV.divide(total_area_sp, nr)
    total_area_io = MV.divide(total_area_io, nr)

    # Annual cycle
    total_area_arctic.setAxis(0, t)
    cdutil.setTimeBoundsMonthly(total_area_arctic)
    annual_cycle_arctic = cdutil.ANNUALCYCLE.climatology(total_area_arctic)

    total_area_antarctic.setAxis(0, t)
    cdutil.setTimeBoundsMonthly(total_area_antarctic)
    annual_cycle_antarctic = cdutil.ANNUALCYCLE.climatology(total_area_antarctic)

    total_area_ca.setAxis(0, t)
    cdutil.setTimeBoundsMonthly(total_area_ca)
    annual_cycle_ca = cdutil.ANNUALCYCLE.climatology(total_area_ca)

    total_area_na.setAxis(0, t)
    cdutil.setTimeBoundsMonthly(total_area_na)
    annual_cycle_na = cdutil.ANNUALCYCLE.climatology(total_area_na)

    total_area_np.setAxis(0, t)
    cdutil.setTimeBoundsMonthly(total_area_np)
    annual_cycle_np = cdutil.ANNUALCYCLE.climatology(total_area_np)

    total_area_sa.setAxis(0, t)
    cdutil.setTimeBoundsMonthly(total_area_sa)
    annual_cycle_sa = cdutil.ANNUALCYCLE.climatology(total_area_sa)

    total_area_sp.setAxis(0, t)
    cdutil.setTimeBoundsMonthly(total_area_sp)
    annual_cycle_sp = cdutil.ANNUALCYCLE.climatology(total_area_sp)

    total_area_io.setAxis(0, t)
    cdutil.setTimeBoundsMonthly(total_area_io)
    annual_cycle_io = cdutil.ANNUALCYCLE.climatology(total_area_io)

    ann_arctic[:, i] = np.array(annual_cycle_arctic)
    ann_antarctic[:, i] = np.array(annual_cycle_antarctic)
    ann_ca[:, i] = np.array(annual_cycle_ca)
    ann_na[:, i] = np.array(annual_cycle_na)
    ann_np[:, i] = np.array(annual_cycle_np)
    ann_sa[:, i] = np.array(annual_cycle_sa)
    ann_sp[:, i] = np.array(annual_cycle_sp)
    ann_io[:, i] = np.array(annual_cycle_io)

    # Calculating the CMIP5 STD

    std_arctic[:, i] = np.array(total_area_arctic)
    std_antarctic[:, i] = np.array(total_area_antarctic)
    std_ca[:, i] = np.array(total_area_ca)
    std_na[:, i] = np.array(total_area_na)
    std_np[:, i] = np.array(total_area_np)
    std_sa[:, i] = np.array(total_area_sa)
    std_sp[:, i] = np.array(total_area_sp)
    std_io[:, i] = np.array(total_area_io)

    ann_arctic_mma = ann_arctic_mma + np.array(annual_cycle_arctic)
    ann_antarctic_mma = ann_antarctic_mma + np.array(annual_cycle_antarctic)
    ann_ca_mma = ann_ca_mma + np.array(annual_cycle_ca)
    ann_na_mma = ann_na_mma + np.array(annual_cycle_na)
    ann_np_mma = ann_np_mma + np.array(annual_cycle_np)
    ann_sa_mma = ann_sa_mma + np.array(annual_cycle_sa)
    ann_sp_mma = ann_sp_mma + np.array(annual_cycle_sp)
    ann_io_mma = ann_io_mma + np.array(annual_cycle_io)
    nm = nm + 1

    # Calculating the CMIP5 RMS
    for j in range(0, 2):
        rms_ann_arctic[j, i] = genutil.statistics.rms(
            ann_arctic[:, i], annual_cycle_obs_arctic[:, j], axis=0
        )
        rms_ann_antarctic[j, i] = genutil.statistics.rms(
            ann_antarctic[:, i], annual_cycle_obs_antarctic[:, j], axis=0
        )
        rms_ann_ca[j, i] = genutil.statistics.rms(
            ann_ca[:, i], annual_cycle_obs_ca[:, j], axis=0
        )
        rms_ann_na[j, i] = genutil.statistics.rms(
            ann_na[:, i], annual_cycle_obs_na[:, j], axis=0
        )
        rms_ann_np[j, i] = genutil.statistics.rms(
            ann_np[:, i], annual_cycle_obs_np[:, j], axis=0
        )
        rms_ann_sa[j, i] = genutil.statistics.rms(
            ann_sa[:, i], annual_cycle_obs_sa[:, j], axis=0
        )
        rms_ann_sp[j, i] = genutil.statistics.rms(
            ann_sp[:, i], annual_cycle_obs_sp[:, j], axis=0
        )
        rms_ann_io[j, i] = genutil.statistics.rms(
            ann_io[:, i], annual_cycle_obs_io[:, j], axis=0
        )


# CMIP5 MME
ann_arctic_mma = ann_arctic_mma / nm
ann_antarctic_mma = ann_antarctic_mma / nm
ann_ca_mma = ann_ca_mma / nm
ann_na_mma = ann_na_mma / nm
ann_np_mma = ann_np_mma / nm
ann_sa_mma = ann_sa_mma / nm
ann_sp_mma = ann_sp_mma / nm
ann_io_mma = ann_io_mma / nm

[ni, nj] = std_arctic.shape
tta_std_arctic = MV.zeros([12, 324 / 12, len(mods)])
tta_std_antarctic = MV.zeros([12, 324 / 12, len(mods)])
tta_std_ca = MV.zeros([12, 324 / 12, len(mods)])
tta_std_na = MV.zeros([12, 324 / 12, len(mods)])
tta_std_np = MV.zeros([12, 324 / 12, len(mods)])
tta_std_sa = MV.zeros([12, 324 / 12, len(mods)])
tta_std_sp = MV.zeros([12, 324 / 12, len(mods)])
tta_std_io = MV.zeros([12, 324 / 12, len(mods)])

for im in range(0, 12):
    tta_std_arctic[im, :, :] = std_arctic[im:ni:12, :]
    tta_std_antarctic[im, :, :] = std_antarctic[im:ni:12, :]
    tta_std_ca[im, :, :] = std_ca[im:ni:12, :]
    tta_std_na[im, :, :] = std_na[im:ni:12, :]
    tta_std_np[im, :, :] = std_np[im:ni:12, :]
    tta_std_sa[im, :, :] = std_sa[im:ni:12, :]
    tta_std_sp[im, :, :] = std_sp[im:ni:12, :]
    tta_std_io[im, :, :] = std_io[im:ni:12, :]

[nt, nx, ny] = tta_std_arctic.shape
ttta_std_arctic = MV.reshape(tta_std_arctic, (nt, nx * ny))
ttta_std_ca = MV.reshape(tta_std_ca, (nt, nx * ny))
ttta_std_na = MV.reshape(tta_std_na, (nt, nx * ny))
ttta_std_np = MV.reshape(tta_std_np, (nt, nx * ny))
[nt, nx, ny] = tta_std_antarctic.shape
ttta_std_antarctic = MV.reshape(tta_std_antarctic, (nt, nx * ny))
ttta_std_sa = MV.reshape(tta_std_sa, (nt, nx * ny))
ttta_std_sp = MV.reshape(tta_std_sp, (nt, nx * ny))
ttta_std_io = MV.reshape(tta_std_io, (nt, nx * ny))

for im in range(0, 12):
    annual_cycle_std_mod_arctic[im] = np.array(
        genutil.statistics.std(ttta_std_arctic[im, :])
    )
    annual_cycle_std_mod_antarctic[im] = np.array(
        genutil.statistics.std(ttta_std_antarctic[im, :])
    )
    annual_cycle_std_mod_ca[im] = np.array(genutil.statistics.std(ttta_std_ca[im, :]))
    annual_cycle_std_mod_na[im] = np.array(genutil.statistics.std(ttta_std_na[im, :]))
    annual_cycle_std_mod_np[im] = np.array(genutil.statistics.std(ttta_std_np[im, :]))
    annual_cycle_std_mod_sa[im] = np.array(genutil.statistics.std(ttta_std_sa[im, :]))
    annual_cycle_std_mod_sp[im] = np.array(genutil.statistics.std(ttta_std_sp[im, :]))
    annual_cycle_std_mod_io[im] = np.array(genutil.statistics.std(ttta_std_io[im, :]))

# Plot

# Bar Plots of the RMS
labels = [
    "ACCESS1-3",
    "BNU-ESM",
    "CCSM4",
    "CESM1-BGC",
    "CESM1-CAM5-1-FV2",
    "CESM1-CAM5",
    "CESM1-FASTCHEM",
    "CNRM-CM5",
    "CSIRO-Mk3-6-0",
    "CanCM4",
    "CanESM2",
    "GFDL-CM2p1",
    "GFDL-CM3",
    "GFDL-ES\
M2G",
    "GFDL-ESM2M",
    "GISS-E2-H-CC",
    "GISS-E2-H",
    "GISS-E2-R-CC",
    "GISS-E2-R",
    "HadCM3",
    "HadGEM2-AO",
    "HadGEM2-CC",
    "HadGEM2-ES",
    "IPSL-CM5A-MR",
    "IPSL-CM5B-LR",
    "MIROC-ESM-CHEM",
    "MI\
ROC-ESM",
    "MIROC4h",
    "MIROC5",
    "MPI-ESM-LR",
    "MPI-ESM-MR",
    "MPI-ESM-P",
    "NorESM1-ME",
    "bcc-csm1-1-m",
    "bcc-csm1-1",
]
# labels=["CCSM4","CESM1-BGC","CESM1-CAM5-1-FV2","CESM1-CAM5","CESM1-FASTCHEM","CNRM-CM5","CSIRO-Mk3-6-0","CanCM4","CanESM2","GFDL-CM3","GFDL-ES\
# M2G","GFDL-ESM2M","GISS-E2-H-CC","GISS-E2-H","GISS-E2-R","HadCM3","HadGEM2-CC","HadGEM2-ES","IPSL-CM5A-MR","IPSL-CM5B-LR","MIROC-ESM-CHEM","MI\
# ROC-ESM","MIROC4h","MIROC5","MPI-ESM-LR","MPI-ESM-MR","MPI-ESM-P","NorESM1-ME","bcc-csm1-1"]
# labels=["HadCM3","HadGEM2-CC"]
mlabels = np.append(labels, "RMS-Obs")
rms_arctic = np.append(rms_ann_arctic[0, :], rms_arctic_obs)
rms_antarctic = np.append(rms_ann_antarctic[0, :], rms_antarctic_obs)
rms_ca = np.append(rms_ann_ca[0, :], rms_ca_obs)
rms_na = np.append(rms_ann_na[0, :], rms_na_obs)
rms_np = np.append(rms_ann_np[0, :], rms_np_obs)
rms_sa = np.append(rms_ann_sa[0, :], rms_sa_obs)
rms_sp = np.append(rms_ann_sp[0, :], rms_sp_obs)
rms_io = np.append(rms_ann_io[0, :], rms_io_obs)


ind = np.arange(len(mods))  # the x locations for the groups
# ind = np.arange(len(mods)+1)  # the x locations for the groups
width = 0.3
n = len(ind) - 1

# fig1 = plt.figure(1)
plt.subplot(411)
plt.bar(ind, rms_ann_arctic[0, :], width, color="r")
plt.hold
plt.bar(ind[n] + 2.5 * width, rms_arctic_obs, width, color="b")
plt.xticks(ind + width / 2.0, mlabels, rotation=20, size=8)
# plt.xticks(ind[n]+3*width,mlabels[n+1],rotation=20)
# plt.text
plt.hold
# plt.ylim(0.,ymax)
plt.ylabel("RMS of Total Sea Ice Area, 10${^6}$km${^2}$")
# plt.title('Arctic')
plt.annotate("Arctic", (0.5, 0.9), xycoords="axes fraction", size=15)
plt.grid(True)
# plt.legend(mods_obs,bbox_to_anchor=(0.0, 0., 1, 1), bbox_transform=plt.gcf().transFigure)

# fig2 = plt.figure(2)
plt.subplot(412)
plt.bar(ind, rms_ann_ca[0, :], width, color="r")
plt.bar(ind[n] + 2.5 * width, rms_ca_obs, width, color="b")
# plt.bar(ind+width,rms_ann_na[1,:],width,color='b')
plt.xticks(ind + width / 2.0, mlabels, rotation=20, size=8)
# plt.xticks(ind[n]+3*width,mlabels[n+1],rotation=20)
plt.ylabel("RMS of Total Sea Ice Area, 10${^6}$km${^2}$")
# plt.title('Central Arctic Sector')
plt.annotate("Central Arctic Sector", (0.4, 0.9), xycoords="axes fraction", size=15)
plt.grid(True)
plt.hold

# fig3 = plt.figure(3)
plt.subplot(413)
plt.bar(ind, rms_ann_na[0, :], width, color="r")
plt.bar(ind[n] + 2.5 * width, rms_na_obs, width, color="b")
# plt.bar(ind+width,rms_ann_na[1,:],width,color='b')
plt.xticks(ind + width / 2.0, mlabels, rotation=20, size=8)
# plt.xticks(ind[n]+3*width,mlabels[n+1],rotation=20)
plt.ylabel("RMS of Total Sea Ice Area, 10${^6}$km${^2}$")
# plt.title('North Atlantic Arctic Sector')
plt.annotate(
    "North Atlantic Arctic Sector", (0.4, 0.9), xycoords="axes fraction", size=15
)
plt.grid(True)
plt.hold

# fig4 = plt.figure(4)
plt.subplot(414)
plt.bar(ind, rms_ann_np[0, :], width, color="r")
# Plot the  annual cycle
plt.bar(ind[n] + 2.5 * width, rms_np_obs, width, color="b")
# plt.bar(ind+width,rms_ann_np[1,:],width,color='b')
plt.xticks(ind + width / 2.0, mlabels, rotation=20, size=8)
# plt.xticks(ind[n]+3*width,mlabels[n+1],rotation=20)
plt.hold
# plt.ylim(0.,ymax)
plt.ylabel("RMS of Total Sea Ice Area, 10${^6}$km${^2}$")
# plt.title('North Pacific Arctic Sector')
plt.annotate(
    "North Pacific Arctic Sector", (0.4, 0.9), xycoords="axes fraction", size=15
)
plt.grid(True)
# plt.legend(mods_obs,loc=(.55,0.65))

plt.show()

# Antarctic
fig5 = plt.figure(5)
plt.subplot(411)
plt.bar(ind, rms_ann_antarctic[0, :], width, color="r")
plt.bar(ind[n] + 2.5 * width, rms_antarctic_obs, width, color="b")
# plt.bar(ind+width,rms_ann_antarctic[1,:],width,color='b')
plt.xticks(ind + width / 2.0, mlabels, rotation=20, size=8)
# plt.xticks(ind[n]+3*width,mlabels[n+1],rotation=20)
plt.hold
# plt.ylim(0.,ymax)
plt.ylabel("RMS of Total Sea Ice Area, 10${^6}$km${^2}$")
# plt.title('Antarctic')
plt.annotate("Antarctic", (0.5, 0.9), xycoords="axes fraction", size=15)
# plt.legend(mods_obs,bbox_to_anchor=(0.0, 0., 1, 1), bbox_transform=plt.gcf().transFigure)
plt.grid(True)

# fig6 = plt.figure(6)
plt.subplot(412)
plt.bar(ind, rms_ann_sa[0, :], width, color="r")
plt.bar(ind[n] + 2.5 * width, rms_sa_obs, width, color="b")
# plt.bar(ind+width,rms_ann_sa[1,:],width,color='b')
plt.xticks(ind + width / 2.0, mlabels, rotation=20, size=8)
# plt.xticks(ind[n]+3*width,mlabels[n+1],rotation=20)
plt.hold
# plt.ylim(0.,ymax)
plt.ylabel("RMS of Total Sea Ice Area, 10${^6}$km${^2}$")
# plt.title('South Atlantic Antarctic Sector')
plt.annotate(
    "South Atlantic Ocean Antarctic Sector",
    (0.4, 0.9),
    xycoords="axes fraction",
    size=15,
)
plt.grid(True)

# fig7 = plt.figure(7)
plt.subplot(413)
plt.bar(ind, rms_ann_sp[0, :], width, color="r")
plt.bar(ind[n] + 2.5 * width, rms_sp_obs, width, color="b")
# plt.bar(ind+width,rms_ann_sp[1,:],width,color='b')
plt.xticks(ind + width / 2.0, mlabels, rotation=20, size=8)
plt.hold
# plt.ylim(0.,ymax)
plt.ylabel("RMS of Total Sea Ice Area, 10${^6}$km${^2}$")
# plt.title('South Pacific Antarctic Sector')
plt.annotate(
    "South Pacific Ocean Antarctic Sector",
    (0.4, 0.9),
    xycoords="axes fraction",
    size=15,
)
# plt.legend(obs_mods,loc=(.05,0.65))
plt.grid(True)

# fig8 = plt.figure(8)
plt.subplot(414)
plt.bar(ind, rms_ann_io[0, :], width, color="r")
plt.bar(ind[n] + 2.5 * width, rms_io_obs, width, color="b")
# plt.bar(ind+width,rms_ann_io[1,:],width,color='b')
plt.xticks(ind + width / 2.0, mlabels, rotation=20, size=8)
# plt.xticks(ind[n]+3*width,mlabels[n+1],rotation=20)
plt.hold

plt.ylabel("RMS of Total Sea Ice Area, 10${^6}$km${^2}$")
plt.annotate(
    "South Indian Ocean Antarctic Sector", (0.4, 0.9), xycoords="axes fraction", size=15
)
# plt.title('South Indian Ocean Antarctic Sector')
plt.grid(True)

plt.show()
