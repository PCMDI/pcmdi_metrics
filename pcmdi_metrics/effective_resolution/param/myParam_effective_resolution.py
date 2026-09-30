"""Parameter file for the effective resolution driver.

Edit the values below and run::

    python effective_resolution_driver.py -p param/myParam_effective_resolution.py

Data requirements
-----------------
6-hourly (or higher frequency) instantaneous zonal and meridional wind on
pressure levels, on the model's **native horizontal grid**.  In CMIP6 the
relevant table is ``6hrPlevPt`` (``ua``, ``va``).  Do not regrid: the
diagnostic measures the model's own smallest resolved scales, and regridding
overwrites them.
"""

# =================================================
# Background information
# -------------------------------------------------
mip = "cmip6"

# HighResMIP is the natural target: models are run at two or three resolutions.
exps = ["highresSST-present"]

debug = False

# =================================================
# Models
# -------------------------------------------------
# The 13 configurations of Klaver et al. Table 1, under their ESGF source_id
# names (the paper uses pre-publication HighResMIP labels).
models = [
    "HadGEM3-GC31-LM",
    "HadGEM3-GC31-MM",
    "HadGEM3-GC31-HM",
    "CMCC-CM2-HR4",
    "CMCC-CM2-VHR4",
    "ECMWF-IFS-LR",
    "ECMWF-IFS-HR",
    "EC-Earth3P",
    "EC-Earth3P-HR",
    "MPI-ESM1-2-HR",
    "MPI-ESM1-2-XR",
    "CNRM-CM6-1",
    "CNRM-CM6-1-HR",
]

first_member_only = True

# Fallback when xsearch is unavailable; %(...) fields are filled by the driver.
path_template = None

# Input variables
uvar = "ua"
vvar = "va"
freq = "6hr"
cmipTable = "6hrPlevPt"

# Pressure levels in hPa. Klaver et al. use the divergent spectrum at 250 hPa
# and the rotational spectra at 250 and 500 hPa; the divergent spectrum at
# 500 hPa is computed but deliberately not used for detection.
levels = (250.0, 500.0)

# Klaver et al. sample four months of 2014 to span the seasonal cycle.
# Spectral slopes barely differ between months, so the diagnosed effective
# resolution behaves as a time-invariant model property -- but sampling all
# four is a cheap way to confirm that for a new model.
periods = [
    ("2014-03-01", "2014-03-31"),
    ("2014-06-01", "2014-06-30"),
    ("2014-09-01", "2014-09-30"),
    ("2014-12-01", "2014-12-31"),
]

# =================================================
# Spectral transform
# -------------------------------------------------
# "auto" inspects the latitude spacing. Set explicitly for Gaussian grids
# whose coordinates round to look evenly spaced.
gridtype = "auto"

# Triangular truncation. None -> nlat - 1. Klaver et al. truncate below the
# model's own limit both to save cost and because grid-point-model spectral
# coefficients lose accuracy near the truncation wavenumber.
ntrunc = None

# For reduced Gaussian and octahedral grids (e.g. ECMWF-IFS TCO), the
# Dataset's rectilinear coordinates misrepresent the native mesh. Supply the
# native value here, keyed by model, or leave the entry out to derive it from
# the file. Reference values from Klaver et al. Table 1, in km:
grid_box_distance_km = {
    "HadGEM3-GC31-LM": 217.0,
    "HadGEM3-GC31-MM": 96.7,
    "HadGEM3-GC31-HM": 40.8,
    "CMCC-CM2-HR4": 153.0,
    "CMCC-CM2-VHR4": 38.2,
    "ECMWF-IFS-LR": 79.6,
    "ECMWF-IFS-HR": 40.4,
    "EC-Earth3P": 107.0,
    "EC-Earth3P-HR": 54.2,
    "MPI-ESM1-2-HR": 134.0,
    "MPI-ESM1-2-XR": 66.9,
    "CNRM-CM6-1": 207.0,
    "CNRM-CM6-1-HR": 75.3,
}

# =================================================
# Detection criterion
# -------------------------------------------------
# Sliding fit of E = C * l**(-n) over this many wavenumbers (Appendix S3).
fit_window = 20

# Which wavenumber in the window the fitted exponent is assigned to. The paper
# is ambiguous; "center" is conventional, "right" is the literal reading of
# "steepening at the largest wavenumber in the range".
fit_anchor = "center"

# Required fractional increase of the exponent n over a wavenumber_ratio
# increase in l. The authors call 0.25 "ad hoc and somewhat arbitrary" and
# argue the two-of-three rule makes the answer only marginally sensitive to
# it -- worth re-testing on any model not in their set.
steepening_factor = 0.25
wavenumber_ratio = 2.0

# Smallest wavenumber at which detection is attempted (dS ~ 625 km). Below
# l = 13 the observed spectrum is shallower than k**-3, so the method is not
# meaningful there. A model showing no steepening by l = 32 gets an upper
# limit, not a value.
min_wavenumber = 32

# Number of the three spectra that must steepen. 2 of 3 is the median.
n_confirm = 2

# =================================================
# Output
# -------------------------------------------------
result_dir = "output_debug" if debug else "output"

save_netcdf = True
save_json = True
plot = True
