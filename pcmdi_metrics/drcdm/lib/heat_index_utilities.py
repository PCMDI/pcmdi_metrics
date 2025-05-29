import numpy as np

## Functions to help calculate daily max heat index from hourly relative humidity/dewpoint and temperature files

# HI = -42.379 + 2.04901523T + 10.14333127R - 0.22475541TR - 6.83783x10-3T2
# - 5.481717x10-2R2 + 1.22874x10-3T2R + 8.5282x10-4TR2 - 1.99x10-6T2R2


def degF_to_degC(t):
    return (t - 32) * 5 / 9


def calculate_rh(t, td, units="degF"):
    """Calculate relative humidity from temperature and dewpoint."""
    if units == "degF":
        t = degF_to_degC(t)
        td = degF_to_degC(td)
    # Saturation vapor pressure (e_s) in hPa
    e_s = 6.112 * np.exp((17.67 * t) / (t + 243.5))

    # Actual vapor pressure (e) in hPa
    e = 6.112 * np.exp((17.67 * td) / (td + 243.5))

    # Relative Humidity (RH) in percentage
    rh = 100 * (e / e_s)
    return rh


def heat_index(t, rh):
    # Coefficients for the heat index formula
    c1 = -42.379
    c2 = 2.04901523
    c3 = 10.14333127
    c4 = -0.22475541
    c5 = -6.83783 * 10 ** (-3)
    c6 = -5.481717 * 10 ** (-2)
    c7 = 1.22874 * 10 ** (-3)
    c8 = 8.5282 * 10 ** (-4)
    c9 = -1.99 * 10 ** (-6)

    # Heat index calculation
    return (
        c1
        + c2 * t
        + c3 * rh
        + c4 * t * rh
        + c5 * t**2
        + c6 * rh**2
        + c7 * t**2 * rh
        + c8 * t * rh**2
        + c9 * t**2 * rh**2
    )
