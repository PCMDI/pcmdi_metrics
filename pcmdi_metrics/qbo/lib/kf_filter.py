# This script is from https://github.com/tmiyachi/mcclimate/blob/master/kf_filter.py
# 2023-10 taper_to_mean option added by Jiwoo Lee (LLNL)
# 2024-04 NaN value removal added by Jiwoo Lee (LLNL)

import sys

import numpy
import scipy.fftpack as fftpack
import scipy.signal as signal

from . import const

NA = numpy.newaxis
pi = numpy.pi
g = const.gravity_earth
a = const.radius_earth
beta = 2.0 * const.omega_earth / const.radius_earth


class KFfilter:
    """Wavenumber-frequency filtering following Wheeler and Kiladis (1999)
    and Wheeler, Kiladis and Hendon (2000).

    Detrends and tapers the input data in time, then Fourier-transforms it
    in time and longitude. The `kfmask`/`wavefilter` methods and the
    named per-wave-type filters (`kelvinfilter`, `erfilter`, `igfilter`,
    `eig0filter`, `mrgfilter`, `tdfilter`) mask out all wavenumber-frequency
    content outside a given domain and inverse-transform back to physical
    space.

    Attributes
    ----------
    detrended : numpy.ndarray
        Input data with the along-time linear trend removed.
    window : numpy.ndarray
        1-D time-tapering window applied to `detrended`.
    tapered : numpy.ndarray
        `detrended` after the time-tapering window has been applied.
    fftdata : numpy.ndarray
        2-D (time, longitude) FFT of `tapered`, shape (frequency,
        latitude, wavenumber).
    knum : numpy.ndarray
        Zonal wavenumber at each (frequency, wavenumber) FFT bin.
    freq : numpy.ndarray
        Absolute frequency (cycles per day) at each (frequency,
        wavenumber) FFT bin.
    wavenumber : numpy.ndarray
        1-D zonal wavenumber axis.
    frequency : numpy.ndarray
        1-D frequency axis (cycles per day).
    """

    def __init__(self, datain, spd, tim_taper=0.1, taper_to_mean=False):
        """
        Parameters
        ----------
        datain : numpy.ndarray
            Data to be filtered, with dimensions ``(time, lat, lon)``.
        spd : int
            Samples per day.
        tim_taper : float or {"hann"}, optional
            Tapering ratio applied by a cosine taper to the first and last
            ``tim_taper`` fraction of samples (default is cos20 tapering).
            If ``"hann"``, a Hann window is applied instead. Default is
            ``0.1``.
        taper_to_mean : bool, optional
            If ``True``, taper toward the time-mean instead of toward
            zero. Default is ``False``.
        """
        ntim, nlat, nlon = datain.shape

        # remove the lowest three harmonics of the seasonal cycle (WK99, WKW03)
        ##         if ntim > 365*spd/3:
        ##             rf = fftpack.rfft(datain,axis=0)
        ##             freq = fftpack.rfftfreq(ntim*spd, d=1./float(spd))
        ##             rf[(freq <= 3./365) & (freq >=1./365),:,:] = 0.0     #freq<=3./365 only??
        ##             datain = fftpack.irfft(rf,axis=0)

        # remove NaN value if exist in datain
        nan_mask = numpy.isnan(datain)  # Identify NaN values
        datain[nan_mask] = 0  # Replace NaN values with zero

        # remove dominal trend
        data = signal.detrend(datain, axis=0)

        self.detrended = data.copy()

        # tapering
        if tim_taper == "hann":
            window = signal.hann(ntim)
            data = data * window[:, NA, NA]
        elif tim_taper > 0:
            # taper by cos tapering same dtype as input array
            tp = int(ntim * tim_taper)
            window = numpy.ones(ntim, dtype=datain.dtype)
            x = numpy.arange(tp)
            window[:tp] = 0.5 * (1.0 - numpy.cos(x * pi / tp))
            window[-tp:] = 0.5 * (1.0 - numpy.cos(x[::-1] * pi / tp))
            if taper_to_mean is False:
                data = data * window[:, NA, NA]
            else:
                mean = data.mean(axis=0)
                print("mean:", mean)
                data = (data - mean) * window[:, NA, NA] + mean

        self.window = window
        self.tapered = data.copy()

        # FFT
        self.fftdata = fftpack.fft2(data, axes=(0, 2))

        # Note
        # fft is defined by exp(-ikx), so to adjust exp(ikx) multipried minus
        wavenumber = -fftpack.fftfreq(nlon) * nlon
        frequency = fftpack.fftfreq(ntim, d=1.0 / float(spd))
        knum, freq = numpy.meshgrid(wavenumber, frequency)

        # make f<0 domain same as f>0 domain
        # CAUTION: wave definition is exp(i(k*x-omega*t)) but FFT definition exp(-ikx)
        # so cahnge sign
        knum[freq < 0] = -knum[freq < 0]
        freq = numpy.abs(freq)
        self.knum = knum
        self.freq = freq

        self.wavenumber = wavenumber
        self.frequency = frequency

    def decompose_antisymm(self):
        """Decompose `fftdata` into symmetric and antisymmetric components about the equator.

        Replaces `fftdata` in place with the antisymmetric component
        stacked on the symmetric component along the latitude axis.
        """
        fftdata = self.fftdata
        nf, nlat, nk = fftdata.shape
        symm = 0.5 * (
            fftdata[:, : nlat / 2 + 1, :] + fftdata[:, nlat : nlat / 2 - 1 : -1, :]
        )
        anti = 0.5 * (fftdata[:, : nlat / 2, :] - fftdata[:, nlat : nlat / 2 : -1, :])

        self.fftdata = numpy.concatenate([anti, symm], axis=1)

    def kfmask(self, fmin=None, fmax=None, kmin=None, kmax=None):
        """Build a rectangular wavenumber-frequency mask for `wavefilter`.

        Parameters
        ----------
        fmin : float or None, optional
            Minimum frequency to keep, cycles per day. Default is ``None``
            (no lower bound).
        fmax : float or None, optional
            Maximum frequency to keep, cycles per day. Default is ``None``
            (no upper bound).
        kmin : float or None, optional
            Minimum zonal wavenumber to keep. Default is ``None`` (no
            lower bound).
        kmax : float or None, optional
            Maximum zonal wavenumber to keep. Default is ``None`` (no
            upper bound).

        Returns
        -------
        numpy.ndarray
            Boolean mask of shape ``(frequency, wavenumber)``. ``True``
            marks bins to be zeroed out (i.e. filtered away).
        """
        nf, nlat, nk = self.fftdata.shape
        knum = self.knum
        freq = self.freq

        # wavenumber cut-off
        mask = numpy.zeros((nf, nk), dtype=numpy.bool)
        if kmin is not None:
            mask = mask | (knum < kmin)
        if kmax is not None:
            mask = mask | (kmax < knum)

        # frequency cutoff
        if fmin is not None:
            mask = mask | (freq < fmin)
        if fmax is not None:
            mask = mask | (fmax < freq)

        return mask

    def wavefilter(self, mask):
        """Apply a wavenumber-frequency mask and inverse-transform to physical space.

        Parameters
        ----------
        mask : numpy.ndarray
            2-D boolean array of shape ``(frequency, wavenumber)``, e.g.
            from `kfmask`. ``True`` bins are zeroed out; ``False`` bins are
            kept.

        Returns
        -------
        numpy.ndarray
            Filtered data, real part of the inverse FFT, same shape as the
            original ``datain``.
        """
        # wavenumber = self.wavenumber
        # frequency = self.frequency
        fftdata = self.fftdata.copy()
        nf, nlat, nk = fftdata.shape

        if (nf, nk) != mask.shape:
            print("mask array size is incorrect.")
            sys.exit()

        mask = numpy.repeat(mask[:, NA, :], nlat, axis=1)
        fftdata[mask] = 0.0

        # inverse FFT
        filterd = fftpack.ifft2(fftdata, axes=(0, 2))
        return filterd.real

    # filter
    def kelvinfilter(self, fmin=0.05, fmax=0.4, kmin=None, kmax=14, hmin=8, hmax=90):
        """Filter for equatorial Kelvin waves.

        Parameters
        ----------
        fmin : float or None, optional
            Minimum frequency, cycles per day. Default is ``0.05``.
        fmax : float or None, optional
            Maximum frequency, cycles per day. Default is ``0.4``.
        kmin : float or None, optional
            Minimum zonal wavenumber. Default is ``None`` (no lower
            bound).
        kmax : float or None, optional
            Maximum zonal wavenumber. Default is ``14``.
        hmin : float or None, optional
            Minimum equivalent depth, meters. Default is ``8``.
        hmax : float or None, optional
            Maximum equivalent depth, meters. Default is ``90``.

        Returns
        -------
        numpy.ndarray
            Kelvin-wave-filtered data, same shape as the original
            ``datain``.
        """

        fftdata = self.fftdata.copy()
        knum = self.knum
        freq = self.freq
        nf, nlat, nk = fftdata.shape

        # filtering ############################################################
        mask = numpy.zeros((nf, nk), dtype=numpy.bool)
        # wavenumber cut-off
        if kmin is not None:
            mask = mask | (knum < kmin)
        if kmax is not None:
            mask = mask | (kmax < knum)

        # frequency cutoff
        if fmin is not None:
            mask = mask | (freq < fmin)
        if fmax is not None:
            mask = mask | (fmax < freq)

        # dispersion filter
        if hmin is not None:
            c = numpy.sqrt(g * hmin)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega - k < 0)
        if hmax is not None:
            c = numpy.sqrt(g * hmax)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega - k > 0)

        mask = numpy.repeat(mask[:, NA, :], nlat, axis=1)
        fftdata[mask] = 0.0

        filterd = fftpack.ifft2(fftdata, axes=(0, 2))
        return filterd.real

    def erfilter(self, fmin=None, fmax=None, kmin=-10, kmax=-1, hmin=8, hmax=90, n=1):
        """Filter for equatorial Rossby (ER) waves.

        Parameters
        ----------
        fmin : float or None, optional
            Minimum frequency, cycles per day. Default is ``None`` (no
            lower bound).
        fmax : float or None, optional
            Maximum frequency, cycles per day. Default is ``None`` (no
            upper bound).
        kmin : float or None, optional
            Minimum zonal wavenumber. Default is ``-10``.
        kmax : float or None, optional
            Maximum zonal wavenumber. Default is ``-1``.
        hmin : float or None, optional
            Minimum equivalent depth, meters. Default is ``8``.
        hmax : float or None, optional
            Maximum equivalent depth, meters. Default is ``90``.
        n : int, optional
            Meridional mode number, must be a positive integer. Default is
            ``1``.

        Returns
        -------
        numpy.ndarray
            ER-wave-filtered data, same shape as the original ``datain``.
        """

        if n <= 0 or n % 1 != 0:
            print("n must be n>=1 integer")
            sys.exit()

        fftdata = self.fftdata.copy()
        knum = self.knum
        freq = self.freq
        nf, nlat, nk = fftdata.shape

        # filtering ############################################################
        mask = numpy.zeros((nf, nk), dtype=numpy.bool)
        # wavenumber cut-off
        if kmin is not None:
            mask = mask | (knum < kmin)
        if kmax is not None:
            mask = mask | (kmax < knum)

        # frequency cutoff
        if fmin is not None:
            mask = mask | (freq < fmin)
        if fmax is not None:
            mask = mask | (fmax < freq)

        # dispersion filter
        if hmin is not None:
            c = numpy.sqrt(g * hmin)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega * (k**2 + (2 * n + 1)) + k < 0)
        if hmax is not None:
            c = numpy.sqrt(g * hmax)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega * (k**2 + (2 * n + 1)) + k > 0)
        mask = numpy.repeat(mask[:, NA, :], nlat, axis=1)

        fftdata[mask] = 0.0

        filterd = fftpack.ifft2(fftdata, axes=(0, 2))
        return filterd.real

    def igfilter(self, fmin=None, fmax=None, kmin=-15, kmax=-1, hmin=12, hmax=90, n=1):
        """Filter for n>=1 inertio-gravity waves. Default is n=1 (westward IG, WIG).

        For n=0 eastward inertio-gravity waves, use `eig0filter` instead.

        Parameters
        ----------
        fmin : float or None, optional
            Minimum frequency, cycles per day. Default is ``None`` (no
            lower bound).
        fmax : float or None, optional
            Maximum frequency, cycles per day. Default is ``None`` (no
            upper bound).
        kmin : float or None, optional
            Minimum zonal wavenumber; negative is westward, positive is
            eastward. Default is ``-15``.
        kmax : float or None, optional
            Maximum zonal wavenumber. Default is ``-1``.
        hmin : float or None, optional
            Minimum equivalent depth, meters. Default is ``12``.
        hmax : float or None, optional
            Maximum equivalent depth, meters. Default is ``90``.
        n : int, optional
            Meridional mode number, must be a positive integer. Default is
            ``1``.

        Returns
        -------
        numpy.ndarray
            Inertio-gravity-wave-filtered data, same shape as the original
            ``datain``.
        """
        if n <= 0 or n % 1 != 0:
            print("n must be n>=1 integer. for n=0 EIG you must use eig0filter method.")
            sys.exit()

        fftdata = self.fftdata.copy()
        knum = self.knum
        freq = self.freq
        nf, nlat, nk = fftdata.shape

        # filtering ############################################################
        mask = numpy.zeros((nf, nk), dtype=numpy.bool)
        # wavenumber cut-off
        if kmin is not None:
            mask = mask | (knum < kmin)
        if kmax is not None:
            mask = mask | (kmax < knum)

        # frequency cutoff
        if fmin is not None:
            mask = mask | (freq < fmin)
        if fmax is not None:
            mask = mask | (fmax < freq)

        # dispersion filter
        if hmin is not None:
            c = numpy.sqrt(g * hmin)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega**2 - k**2 - (2 * n + 1) < 0)
        if hmax is not None:
            c = numpy.sqrt(g * hmax)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega**2 - k**2 - (2 * n + 1) > 0)
        mask = numpy.repeat(mask[:, NA, :], nlat, axis=1)
        fftdata[mask] = 0.0

        filterd = fftpack.ifft2(fftdata, axes=(0, 2))
        return filterd.real

    def eig0filter(self, fmin=None, fmax=0.55, kmin=0, kmax=15, hmin=12, hmax=50):
        """Filter for n=0 eastward inertio-gravity (EIG0) waves.

        Parameters
        ----------
        fmin : float or None, optional
            Minimum frequency, cycles per day. Default is ``None`` (no
            lower bound).
        fmax : float or None, optional
            Maximum frequency, cycles per day. Default is ``0.55``.
        kmin : float or None, optional
            Minimum zonal wavenumber; must be non-negative (negative ``k``
            for this mode is the mixed Rossby-gravity wave -- see
            `mrgfilter`). Default is ``0``.
        kmax : float or None, optional
            Maximum zonal wavenumber. Default is ``15``.
        hmin : float or None, optional
            Minimum equivalent depth, meters. Default is ``12``.
        hmax : float or None, optional
            Maximum equivalent depth, meters. Default is ``50``.

        Returns
        -------
        numpy.ndarray
            EIG0-wave-filtered data, same shape as the original ``datain``.
        """
        if kmin < 0:
            print("kmin must be positive. if k < 0, this mode is MRG")
            sys.exit()

        fftdata = self.fftdata.copy()
        knum = self.knum
        freq = self.freq
        nf, nlat, nk = fftdata.shape

        # filtering ############################################################
        mask = numpy.zeros((nf, nk), dtype=numpy.bool)
        # wavenumber cut-off
        if kmin is not None:
            mask = mask | (knum < kmin)
        if kmax is not None:
            mask = mask | (kmax < knum)

        # frequency cutoff
        if fmin is not None:
            mask = mask | (freq < fmin)
        if fmax is not None:
            mask = mask | (fmax < freq)

        # dispersion filter
        if hmin is not None:
            c = numpy.sqrt(g * hmin)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega**2 - k * omega - 1 < 0)
        if hmax is not None:
            c = numpy.sqrt(g * hmax)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega**2 - k * omega - 1 > 0)
        mask = numpy.repeat(mask[:, NA, :], nlat, axis=1)
        fftdata[mask] = 0.0

        filterd = fftpack.ifft2(fftdata, axes=(0, 2))
        return filterd.real

    def mrgfilter(self, fmin=None, fmax=None, kmin=-10, kmax=-1, hmin=8, hmax=90):
        """Filter for mixed Rossby-gravity (MRG) waves.

        Parameters
        ----------
        fmin : float or None, optional
            Minimum frequency, cycles per day. Default is ``None`` (no
            lower bound).
        fmax : float or None, optional
            Maximum frequency, cycles per day. Default is ``None`` (no
            upper bound).
        kmin : float or None, optional
            Minimum zonal wavenumber; negative is westward, positive is
            eastward. Default is ``-10``.
        kmax : float or None, optional
            Maximum zonal wavenumber; must be non-positive (positive ``k``
            for this mode is the n=0 eastward inertio-gravity wave -- see
            `eig0filter`). Default is ``-1``.
        hmin : float or None, optional
            Minimum equivalent depth, meters. Default is ``8``.
        hmax : float or None, optional
            Maximum equivalent depth, meters. Default is ``90``.

        Returns
        -------
        numpy.ndarray
            MRG-wave-filtered data, same shape as the original ``datain``.
        """
        if kmax > 0:
            print("kmax must be negative. if k > 0, this mode is the same as n=0 EIG")
            sys.exit()

        fftdata = self.fftdata.copy()
        knum = self.knum
        freq = self.freq
        nf, nlat, nk = fftdata.shape

        # filtering ############################################################
        mask = numpy.zeros((nf, nk), dtype=numpy.bool)
        # wavenumber cut-off
        if kmin is not None:
            mask = mask | (knum < kmin)
        if kmax is not None:
            mask = mask | (kmax < knum)

        # frequency cutoff
        if fmin is not None:
            mask = mask | (freq < fmin)
        if fmax is not None:
            mask = mask | (fmax < freq)

        # dispersion filter
        if hmin is not None:
            c = numpy.sqrt(g * hmin)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega**2 - k * omega - 1 < 0)
        if hmax is not None:
            c = numpy.sqrt(g * hmax)
            omega = (
                2.0 * pi * freq / 24.0 / 3600.0 / numpy.sqrt(beta * c)
            )  # adusting day^-1 to s^-1
            k = knum / a * numpy.sqrt(c / beta)  # adusting ^2pia to ^m
            mask = mask | (omega**2 - k * omega - 1 > 0)
        mask = numpy.repeat(mask[:, NA, :], nlat, axis=1)
        fftdata[mask] = 0.0

        filterd = fftpack.ifft2(fftdata, axes=(0, 2))
        return filterd.real

    def tdfilter(self, fmin=None, fmax=None, kmin=-20, kmax=-6):
        """Filter for tropical-depression-type (TD-type) disturbances, following KTH05.

        Unlike the other filters, this uses a fixed dispersion-curve
        boundary (not an equivalent-depth range) to isolate the TD-type
        band.

        Parameters
        ----------
        fmin : float or None, optional
            Minimum frequency, cycles per day. Default is ``None`` (no
            lower bound).
        fmax : float or None, optional
            Maximum frequency, cycles per day. Default is ``None`` (no
            upper bound).
        kmin : float or None, optional
            Minimum zonal wavenumber; negative is westward, positive is
            eastward. Default is ``-20``.
        kmax : float or None, optional
            Maximum zonal wavenumber. Default is ``-6``.

        Returns
        -------
        numpy.ndarray
            TD-type-filtered data, same shape as the original ``datain``.
        """
        fftdata = self.fftdata.copy()
        knum = self.knum
        freq = self.freq
        nf, nlat, nk = fftdata.shape
        mask = numpy.zeros((nf, nk), dtype=numpy.bool)

        # wavenumber cut-off
        if kmin is not None:
            mask = mask | (knum < kmin)
        if kmax is not None:
            mask = mask | (kmax < knum)

        # frequency cutoff
        if fmin is not None:
            mask = mask | (freq < fmin)
        if fmax is not None:
            mask = mask | (fmax < freq)

        # dispersion filter
        mask = mask | (84 * freq + knum - 22 > 0) | (210 * freq + 2.5 * knum - 13 < 0)
        mask = numpy.repeat(mask[:, NA, :], nlat, axis=1)

        fftdata[mask] = 0.0

        filterd = fftpack.ifft2(fftdata, axes=(0, 2))
        return filterd.real


"""
# test #############################################
import matplotlib.pyplot as plt
from scipy.fftpack import fftshift
x = fftshift(self.wavenumber)
y = fftshift(self.frequency)
power = numpy.abs(fftshift(fftdata[:,10,:], axes=(0,1)))**2
z = power
CF=plt.contourf(x,y,z,[0,0.5,1],extend='max')
plt.axis([-17,17,-0.5,0.5])
plt.colorbar(CF)
plt.show()
sys.exit()
"""
