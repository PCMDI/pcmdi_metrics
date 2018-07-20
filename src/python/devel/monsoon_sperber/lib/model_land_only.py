import cdms2
import genutil
import MV2

#def model_land_only(model, model_timeseries, model_lf_path, debug=False):
def model_land_only(model, model_timeseries, lf, debug=False):
    # -------------------------------------------------
    # Mask out over ocean grid 
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # Read model's land fraction
    #f_lf = cdms2.open(model_lf_path)
    #lf = f_lf('sftlf', latitude=(-90, 90))

    if debug:
        import vcs
        x = vcs.init()
        x.plot(model_timeseries)
        x.png('_'.join(['test',model,'beforeMask.png']))

    # Check land fraction variable to see if it meet criteria
    # (0 for ocean, 100 for land, no missing value)
    lat_c = lf.getAxis(0)
    lon_c = lf.getAxis(1)
    lf_id = lf.id

    lf = MV2.array(lf.filled(0.))

    lf.setAxis(0, lat_c)
    lf.setAxis(1, lon_c)
    lf.id = lf_id

    if float(MV2.max(lf)) == 1.:
        lf = lf * 100

    # Matching dimension
    model_timeseries, lf_timeConst = genutil.grower(model_timeseries, lf)

    #opt1 = True
    opt1 = False

    if opt1:  # Masking out partial ocean grids as well
        # Mask out ocean even fractional (leave only pure ocean grid)
        model_timeseries_masked = MV2.masked_where(
            lf_timeConst < 100, model_timeseries)
    else:  # Mask out only full ocean grid & use weighting for partial ocean grid
        model_timeseries_masked = MV2.masked_where(
            lf_timeConst == 0, model_timeseries)  # mask out pure ocean grids
        if model == 'EC-EARTH':
            # Mask out over 90% land grids for models those consider river as
            # part of land-sea fraction. So far only 'EC-EARTH' does..
            model_timeseries_masked = MV2.masked_where(
                lf_timeConst < 90, model_timeseries)
        #lf2 = (100.-lf)/100.
        lf2 = MV2.divide(lf,100.)
        model_timeseries, lf2_timeConst = genutil.grower(
            model_timeseries, lf2)  # Matching dimension
        model_timeseries_masked = model_timeseries_masked * \
            lf2_timeConst  # consider land fraction like as weighting

    if debug:
        x.clear()
        x.plot(model_timeseries_masked)
        x.png('_'.join(['test',model,'afterMask.png']))
        x.close()

    return(model_timeseries_masked)
