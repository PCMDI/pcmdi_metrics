libfiles = ['lib_mjo.py',
            'plot_wavenumber_frequency_power.py',
            'debug_chk_plot.py']

for lib in libfiles:
    exec(compile(open(os.path.join('../lib/', lib)).read(),
                 os.path.join('../lib/', lib), 'exec'))


def mjo_metric_ewr_calculation(
    debug, plot, nc_out, cmmGrid, degX,
    UnitsAdjust, inputfile, var, startYear, endYear,
    ):


    # Open file to read daily dataset
    if debug: print('debug: open file')
    f = cdms2.open(inputfile)
    d = f[var]
    tim = d.getTime()
    comTim = tim.asComponentTime()
    calendar = tim.calendar

    # Get starting and ending year and month
    if debug: print('debug: check time')
    first_time = comTim[0]
    last_time = comTim[-1]

    # Adjust years to consider only when continous NDJFMA is available
    if first_time > cdtime.comptime(startYear, 11, 1):
        startYear += 1
    if last_time < cdtime.comptime(endYear, 4, 30):
        endYear -= 1

    # Number of grids for 2d fft input
    NL = len(d.getLongitude())  # number of grid in x-axis (longitude)
    if cmmGrid:
        NL = int(360/degX)
    NT = segmentLength  # number of time step for each segment (need to be an even number)

    if debug: endYear = startYear+2
    if debug: print('debug: startYear, endYear:', startYear, endYear)
    if debug: print('debug: NL, NT:', NL, NT)

    #
    # Get daily climatology on each grid, then remove it to get anomaly
    #
    numYear = endYear - startYear
    mon = 11
    day = 1
    # Store each year's segment in a dictionary: segment[year]
    segment = {}
    segment_ano = {}
    daSeaCyc = MV2.zeros((NT, d.shape[1], d.shape[2]), MV2.float)
    for year in range(startYear, endYear):
        print(year)
        segment[year] = subSliceSegment(d, year, mon, day, NT)
        # units conversion
        segment[year] = unit_conversion(segment[year], UnitsAdjust)
        # Get climatology of daily seasonal cycle
        daSeaCyc = MV2.add(
            MV2.divide(segment[year],float(numYear)),
            daSeaCyc)
    # Remove daily seasonal cycle from each segment
    if numYear > 1:
        for year in range(startYear, endYear):
            segment_ano[year] = Remove_dailySeasonalCycle(segment[year], daSeaCyc)

    #
    # Space-time power spectra
    #
    """
    Handle each segment (i.e. each year) separately.
    1. Get daily time series (3D: time and spatial 2D)
    2. Meridionally average (2D: time and spatial, i.e., longitude) 
    3. Get anomaly by removing time mean of the segment
    4. Proceed 2-D FFT to get power.
    Then get multi-year averaged power after the year loop.
    """
    # Define array for archiving power from each year segment
    Power = np.zeros((numYear, NT + 1, NL + 1), np.float)

    # Year loop for space-time spectrum calculation
    if debug: print('debug: year loop start')
    for n, year in enumerate(range(startYear, endYear)):
        print('chk: year:', year)
        d_seg = segment_ano[year]
        # Regrid: interpolation to common grid
        if cmmGrid:
            d_seg = interp2commonGrid(d_seg, degX, debug=debug)
        # Subregion, meridional average, and remove segment time mean
        d_seg_x_ano = get_daily_ano_segment(d_seg)
        # Compute space-time spectrum
        if debug: print('debug: compute space-time spectrum')
        Power[n, :, :] = space_time_spectrum(d_seg_x_ano)

    # Multi-year averaged power
    Power = np.average(Power, axis=0)
    # Generates axes for the decoration
    Power, ff, ss = generate_axes_and_decorate(Power, NT, NL)
    # Output for wavenumber-frequency power spectra
    OEE = output_power_spectra(NL, NT, Power, ff, ss)

    # E/W ratio
    ewr, eastPower, westPower = calculate_ewr(OEE)
    print('ewr: ', ewr)
    print('east power: ', eastPower)
    print('west power: ', westPower)

    # Output
    output_filename = "{}_{}_{}_{}_{}_{}-{}".format(
        mip, model, exp,
        run, 'mjo', startYear, endYear)
    if cmmGrid:
        output_filename += '_cmmGrid'

    # NetCDF output
    if nc_out:
        if not os.path.exists(outdir(output_type='diagnostic_results')):
            os.makedirs(outdir(output_type='diagnostic_results'))
        fout = os.path.join(
            outdir(output_type='diagnostic_results'),
            output_filename)
        write_netcdf_output(OEE, fout)

    # Plot
    if plot:
        if not os.path.exists(outdir(output_type='graphics')):
            os.makedirs(outdir(output_type='graphics'))
        fout = os.path.join(
            outdir(output_type='graphics'),
            output_filename)
        title = mip.upper()+': '+model+' ('+run+') \n'+var.capitalize()+', NDJFMA '+str(startYear)+'-'+str(endYear) 
        if cmmGrid:
            title += ', common grid (2.5x2.5deg)'
        plot_power(OEE, title, fout, ewr)

    # Output to JSON
    metrics_result = {}
    metrics_result['east_power'] = eastPower
    metrics_result['west_power'] = westPower
    metrics_result['east_west_power_ratio'] = ewr
    metrics_result['analysis_time_window_start_year'] = startYear
    metrics_result['analysis_time_window_end_year'] = endYear

    # Debug checking plot
    if debug and plot:
        debug_chk_plot()

    f.close()
    return metrics_result
