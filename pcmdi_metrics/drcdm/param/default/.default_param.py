# Settings for extremes driver
# JSON Description goes here

# These settings are required
test_data_set = ["%(source_name)"]
vars = ["%(varname)"]
realization = ["%(realization)"]
test_data_path = "%(path_dir)"
filename_template = "%(file_path)"

# metrics_output_path = "/pscratch/sd/j/jsgoodni/pmp_results/drcdm/LOCA2/"

metrics_output_path = "/pscratch/sd/j/jsgoodni/pmp_results/drcdm/%(source_name)/"

# Optional settings
# See the README for more information about these settings

shp_path = "/pscratch/sd/j/jsgoodni/shapefiles/cb_2018_us_state_20m.shp"
attribute = "NAME"
region_name = "California"  # Region name within the shapefile

# coords = [ [235,24], [294,24], [294, 50], [235,50] ]
# sftlf_filename_template = '/p/css03/esgf_publish/CMIP6/CMIP/MIROC/MIROC6/piControl/r1i1p1f1/fx/sftlf/gn/v20190311/sftlf_fx_MIROC6_piControl_r1i1p1f1_gn.nc'

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

# custom_thresholds = {  # accepted units - degF, degC, degK (temp), mm, inches (precip)
#     "tasmin_ge": {"values": [27], "units": "degC"},
#     "tasmin_le": {"values": [-18], "units": "degC"},
#     "tasmax_ge": {"values": [35], "units": "degC"},
#     "tasmax_le": {"values": [10], "units": "degC"},
#     "growing_season": {"values": [32], "units": "degF"}, # also used for first/last day below X
#     "pr_ge": {"values": [25, 50, 100], "units": "mm"},
#     "pr_ge_quant": {"values": [90, 99], "units": "%"},
#     "tmax_days_above_q": {"values": [90, 99], "units": "%"},
#     "tmax_days_below_q": {"values": [1, 10],  "units": "%"},
#     "tmin_days_above_q": {"values": [90, 99], "units": "%"},
#     "tmin_days_below_q": {"values": [1, 10],  "units": "%"},
# }

# Exclude parameter to run all metrics
dec_mode = "DJF"
annual_strict = False
exclude_leap = True
compute_tasmean = True
drop_incomplete_djf = False
regrid = False
plot = True
mode = "climatology"  # Default "climatology"
netcdf = True
generate_sftlf = True
use_dask = False

chunk_lat = 500
chunk_lon = 500
chunk_time = 365

msyear = "%(start_year)"
meyear = "%(end_year)"

# osyear = 1981    # if no obs files provided, needs to be a subset of model year range
# oeyear = 2010
