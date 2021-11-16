def fastFT(x, t):
    """
    Use a Numerical Python function to compute a FAST Fourier transform -- which should give the same result as a simple
    SLOW Fourier integration via the trapezoidal rule.

    Return mean + amplitudes and times-of-maximum of the first three Fourier harmonic components of a time series x(t).
    Do NOT detrend the time series first, in order to retain the "sawtooth" frequency implied by the input length of the
    time series (e.g. the 24-hour period from a composite-diurnal cycle).

    On input: x[i, j] = values at each gridpoint (i) for N times (j), e.g. N = 8 for a 3-hr composite-diurnal cycle
              t[i, j] = timepoints at each gridpoint (i) for N times (j), e.g. Local Standard Times

    On output: c[i] = mean value at each gridpoint (i) in the time series (= constant term in Fourier series)
               maxvalue[i, k] = amplitude at each gridpoint (i) for each Fourier harmonic (k)
               tmax    [i, k] = time of maximum at each gridpoint (i) for each Fourier harmonic (k)

               Curt Covey, PCMDI/LLNL November 2016
                 (from ./fourier.py and ./fourierTestFFT.py)
    """
    import numpy

    nGridPoints = len(x)
    X = numpy.fft.ifft(x)
    a = X.real
    b = X.imag
    S = numpy.sqrt(a ** 2 + b ** 2)
    c = S[:, 0]
    # time of maximum for nth component (n=0 => diurnal, n=1 => semi...)
    tmax = numpy.zeros((nGridPoints, 3))
    # value of maximum for nth component (= 1/2 peak-to-peak amplitude)
    maxvalue = numpy.zeros((nGridPoints, 3))
    for n in range(3):
        # Adding first + last terms, second + second-to-last, ...
        maxvalue[:, n] = S[:, n + 1] + S[:, -n - 1]
        tmax[:, n] = numpy.arctan2(b[:, n + 1], a[:, n + 1])
        tmax[:, n] = tmax[:, n] * 12.0 / (numpy.pi * (n + 1))  # Radians to hours
        tmax[:, n] = tmax[:, n] + t[:, 0]  # GMT to LST
        tmax[:, n] = tmax[:, n] % (24 / (n + 1))
    return c, maxvalue, tmax


def fastAllGridFT(x, t):
    """
    This version of fastFT (see above) does all gridpoints at once.

    Use a Numerical Python function to compute a FAST Fourier transform -- which should give the same result as a simple
    SLOW Fourier integration via the trapezoidal rule.

    Return mean + amplitudes and times-of-maximum of the first three Fourier harmonic components of a time series x(t).
    Do NOT detrend the time series first, in order to retain the "sawtooth" frequency implied by the input length of the
    time series (e.g. the 24-hour period from a composite-diurnal cycle).

    On input: x[k,i,j] = values      at each gridpoint (i,j) for N times (k), e.g. N = 8 for a 3-hr composite-diurnal cycle
          t[k,i,j] = timepoints  at each gridpoint (i,j) for N times (k), e.g. Local Standard Times

    On output: c[i,j] = mean value at each gridpoint (i,j) in the time series ("zeroth" term in Fourier series)
           maxvalue[n,i,j] = amplitude       at each gridpoint (i,j) for each Fourier harmonic (n)
           tmax    [n,i,j] = time of maximum at each gridpoint (i,j) for each Fourier harmonic (n)

                Curt Covey, PCMDI/LLNL                                      December 2016
    """
    import numpy

    print("Creating output arrays ...")
    nx = x.shape[1]
    ny = x.shape[2]
    # time  of maximum for nth component (n=0 => diurnal, n=1 => semi...)
    tmax = numpy.zeros((3, nx, ny))
    # value of maximum for nth component (= 1/2 peak-to-peak amplitude)
    maxvalue = numpy.zeros((3, nx, ny))

    print("Calling numpy FFT function ...")
    X = numpy.fft.ifft(x, axis=0)
    print(X.shape)

    print("Converting from complex-valued FFT to real-valued amplitude and phase ...")
    a = X.real
    b = X.imag
    S = numpy.sqrt(a ** 2 + b ** 2)
    c = S[0]  # Zeroth harmonic = mean-value "constant term" in Fourier series.
    for n in range(3):
        # Adding first + last terms, second + second-to-last, ...
        maxvalue[n] = S[n + 1] + S[-n - 1]
        tmax[n] = numpy.arctan2(b[n + 1], a[n + 1])
        tmax[n] = tmax[n] * 12.0 / (numpy.pi * (n + 1))  # Radians to hours
        tmax[n] = tmax[n] + t[0]  # GMT to LST
        tmax[n] = tmax[n] % (24 / (n + 1))
    return c, maxvalue, tmax
