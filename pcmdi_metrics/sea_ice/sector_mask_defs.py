import MV2 as MV


def getmask(sector, lats, lons, lons_a, lons_p, land_mask):
    # Arctic Regions
    # Central Arctic
    if sector == "ca":
        lat_bound1 = MV.logical_and(MV.greater(lats, 80.0), MV.less_equal(lats, 90.0))
        lat_bound2 = MV.logical_and(MV.greater(lats, 65.0), MV.less_equal(lats, 90.0))
        lon_bound1 = MV.logical_and(
            MV.greater(lons_a, -120.0), MV.less_equal(lons_a, 90.0)
        )
        lon_bound2 = MV.logical_and(
            MV.greater(lons_p, 90.0), MV.less_equal(lons_p, 240.0)
        )
        reg1 = MV.logical_and(lat_bound1, lon_bound1)
        reg2 = MV.logical_and(lat_bound2, lon_bound2)
        mask = MV.where(MV.logical_or(reg1, reg2), 1, 0)
        mask = MV.where(MV.equal(land_mask, 0), 0, mask)  # 0 - Land

    # NA region
    if sector == "na":
        lat_bound = MV.logical_and(MV.greater(lats, 45.0), MV.less_equal(lats, 80.0))
        lon_bound = MV.logical_and(
            MV.greater(lons_a, -120.0), MV.less_equal(lons_a, 90.0)
        )
        lat_bound3 = MV.logical_and(MV.greater(lats, 45.0), MV.less_equal(lats, 50.0))
        lon_bound3 = MV.logical_and(
            MV.greater(lons_a, 30.0), MV.less_equal(lons_a, 60.0)
        )
        reg3 = MV.logical_and(lat_bound3, lon_bound3)

        mask = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)
        mask = MV.where(
            MV.equal(reg3, True), 0, mask
        )  # Masking out the Black and Caspian Seas
        mask = MV.where(MV.equal(land_mask, True), 0, mask)  # 0 - Land
        mask = MV.where(MV.equal(land_mask, 0), 0, mask)  # 0 - Land

    # NP region
    if sector == "np":
        lat_bound = MV.logical_and(MV.greater(lats, 45.0), MV.less_equal(lats, 65.0))
        lon_bound = MV.logical_and(
            MV.greater(lons_p, 90.0), MV.less_equal(lons_p, 240.0)
        )
        mask = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)
        mask = MV.where(MV.equal(land_mask, 0), 0, mask)  # 0 - Land

    # Antarctic Regions

    # SA region
    if sector == "sa":
        lat_bound = MV.logical_and(MV.greater(lats, -90.0), MV.less_equal(lats, -55.0))
        lon_bound = MV.logical_and(
            MV.greater(lons_a, -60.0), MV.less_equal(lons_a, 20.0)
        )
        mask = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)
        mask = MV.where(MV.equal(land_mask, 0), 0, mask)  # 0 - Land

    # SP region
    if sector == "sp":
        lat_bound = MV.logical_and(MV.greater(lats, -90.0), MV.less_equal(lats, -55.0))
        lon_bound = MV.logical_and(
            MV.greater(lons_p, 90.0), MV.less_equal(lons_p, 300.0)
        )
        mask = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)
        mask = MV.where(MV.equal(land_mask, 0), 0, mask)  # 0 - Land

    # IO region
    if sector == "io":
        lat_bound = MV.logical_and(MV.greater(lats, -90.0), MV.less_equal(lats, -55.0))
        lon_bound = MV.logical_and(
            MV.greater(lons_p, 20.0), MV.less_equal(lons_p, 90.0)
        )
        mask = MV.where(MV.logical_and(lat_bound, lon_bound), 1, 0)
        mask = MV.where(MV.equal(land_mask, 0), 0, mask)  # 0 - Land

    return mask
