# Settings for extremes driver
# JSON Description goes here

# These settings are required
test_data_set = ["CanESM5"]  # test for now
vars = ["tasmax"]  # just tasmax for now
realization = ["r1i1p1f1"]
test_data_path = (
    "/global/cfs/projectdirs/m4581/kchang61/carbonplan/data/day/ssp245/????/"
)
filename_template = (
    "ScenarioMIP.*.%(model).ssp245.%(realization).day.DeepSD-BC.%(variable).????.nc"
)

# "ScenarioMIP.{ORG}.{MODEL}.{SCENARIO}.{REALIZATION}.day.{DOWNSCALING METHOD}.{VARIABLE}.{YEAR}.nc"

# metrics_output_path = "/pscratch/sd/j/jsgoodni/pmp_results/drcdm/LOCA2/"

metrics_output_path = "/path/to/scratch/pmp_results/drcdp/s2s/"
# For example - this is what I used
# ("/pscratch/sd/j/jsgoodni/pmp_results/drcdm/kristen-test/")

# Optional settings
# See the README for more information about these settings

# shp_path = "/pscratch/sd/j/jsgoodni/shapefiles/cb_2018_us_state_20m.shp"
# attribute = "NAME"
# region_name = "California"  # Region name within the shapefile

coords = [
    [235, 24],
    [294, 24],
    [294, 50],
    [235, 50],
]  # CONUS, comment out if you need global

ModUnitsAdjust_precip = (
    True,
    "multiply",
    86400,
    "mm",
)  # Convert model units from kg/m2/s to mm/day
# ObsUnitsAdjust_precip = (True, "multiply", 1 / 25.4, "inches")

ModUnitsAdjust_temperature = (True, "multiply", 1, "K")  # Set to False to Leave in K
# ObsUnitsAdjust_temperature = (True, "CtoF", 0, "F")

# Must be a dictionary, since multipy secondary variables could be present. Compatible with structure below
ModUnitsAdjust_other = {}
# ObsUnitsAdjust_other = {}

ModUnitsAdjust = {
    v: (
        ModUnitsAdjust_precip
        if "pr" in v
        else ModUnitsAdjust_temperature
        if "tas" in v
        else ModUnitsAdjust_other[v]
    )
    for v in vars
}

# ObsUnitsAdjust = {
#     v: (
#         ObsUnitsAdjust_precip if "pr" in v
#         else ObsUnitsAdjust_temperature if "tas" in v
#         else ObsUnitsAdjust_other[v]
#     )
#     for v in vars
# }

custom_thresholds = {  # accepted units - degF, degC, degK (temp), mm, inches (precip)
    "monthly_tasmax_ge": {"values": [27], "units": "degC"},
}

include_metrics = [
    "mean_tasmax",
    "monthly_txx",
    "monthly_mean_tasmax",
    "monthly_tasmax_ge",
]

dec_mode = "DJF"
annual_strict = False
exclude_leap = True
compute_tasmean = False
drop_incomplete_djf = False
regrid = False
plot = True
mode = "timeseries"  # Default "climatology" - For s2s we'll want Timeseries mode
netcdf = True
generate_sftlf = True
use_dask = False  # Hopefully shouldn't need dask

chunk_lat = 500
chunk_lon = 500
chunk_time = 365

msyear = 2015  # for ssp245
meyear = 2100

# osyear = 1981    # if no obs files provided, needs to be a subset of model year range
# oeyear = 2010
